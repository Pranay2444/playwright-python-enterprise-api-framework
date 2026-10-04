"""A deliberately small HTTP test double, not a DummyJSON implementation or contract oracle.

It verifies real Playwright transport, client composition, and fixture isolation
without a public dependency. Only the live run can verify DummyJSON behavior.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlsplit


class LocalApi:
    def __init__(self) -> None:
        self.products = [
            {
                "id": 731,
                "title": "Demo Hammer",
                "price": 12.5,
                "category": "tools",
                "stock": 8,
                "rating": 4.3,
                "discountPercentage": 10,
            },
            {
                "id": 947,
                "title": "Demo Drill",
                "price": 40.0,
                "category": "tools",
                "stock": 0,
                "rating": 4.5,
                "discountPercentage": 5,
            },
        ]
        self.user = {
            "id": 503,
            "username": "demo-user",
            "firstName": "Demo",
            "lastName": "User",
            "email": "demo@example.test",
        }
        self.carts = [self.make_cart(811, 503, [{"id": 731, "quantity": 2}])]
        self.requests: list[tuple[str, str]] = []
        self.login_count = 0
        self.refresh_count = 0
        self._access_tokens: set[str] = set()
        self._refresh_tokens: set[str] = set()
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    def make_cart(
        self, cart_id: int, user_id: int, items: list[dict[str, Any]], *, created: bool = False
    ) -> dict[str, Any]:
        discount_field = "discountedPrice" if created else "discountedTotal"
        products = []
        for item in items:
            source = next(p for p in self.products if p["id"] == item["id"])
            total = source["price"] * item["quantity"]
            products.append(
                {
                    "id": source["id"],
                    "title": source["title"],
                    "price": source["price"],
                    "quantity": item["quantity"],
                    "total": total,
                    "discountPercentage": source["discountPercentage"],
                    discount_field: round(total * (100 - source["discountPercentage"]) / 100),
                }
            )
        return {
            "id": cart_id,
            "userId": user_id,
            "products": products,
            "total": sum(p["total"] for p in products),
            "discountedTotal": sum(p[discount_field] for p in products),
            "totalProducts": len(products),
            "totalQuantity": sum(p["quantity"] for p in products),
        }

    @property
    def base_url(self) -> str:
        assert self._server is not None
        return f"http://127.0.0.1:{self._server.server_port}"

    def __enter__(self) -> "LocalApi":
        service = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass  # Avoid noisy body/header logging from the test double.

            def send_json(self, status: int, body: Any, *, cookie: str | None = None) -> None:
                encoded = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                if cookie is not None:
                    self.send_header("Set-Cookie", f"accessToken={cookie}; HttpOnly; Path=/")
                self.end_headers()
                self.wfile.write(encoded)

            def issue_tokens(self) -> dict[str, str]:
                number = service.login_count + service.refresh_count
                access = f"demo-access-{number}"
                refresh = f"demo-refresh-{number}"
                service._access_tokens.add(access)
                service._refresh_tokens.add(refresh)
                return {"accessToken": access, "refreshToken": refresh}

            def do_GET(self) -> None:
                url = urlsplit(self.path)
                query = parse_qs(url.query)
                service.requests.append(("GET", url.path))
                if url.path == "/auth/me":
                    authorization = self.headers.get("Authorization", "")
                    cookie = self.headers.get("Cookie", "")
                    if authorization:
                        allowed = authorization.removeprefix("Bearer ") in service._access_tokens
                    else:
                        allowed = any(f"accessToken={t}" in cookie for t in service._access_tokens)
                    self.send_json(
                        200 if allowed else 401,
                        service.user
                        if allowed
                        else {
                            "message": "Invalid/Expired Token!"
                            if authorization
                            else "Access Token is required"
                        },
                    )
                elif url.path in {"/products", "/products/search"}:
                    products = service.products
                    if url.path.endswith("search"):
                        term = query.get("q", [""])[0].casefold()
                        products = [p for p in products if term in p["title"].casefold()]
                    skip = int(query.get("skip", ["0"])[0])
                    limit = int(query.get("limit", [str(len(products))])[0])
                    selected = products[skip:] if limit == 0 else products[skip : skip + limit]
                    self.send_json(
                        200,
                        {
                            "products": selected,
                            "total": len(products),
                            "skip": skip,
                            "limit": len(selected),
                        },
                    )
                elif url.path.startswith("/products/"):
                    product = next(
                        (p for p in service.products if str(p["id"]) == url.path.split("/")[-1]),
                        None,
                    )
                    self.send_json(200 if product else 404, product or {"message": "Not found"})
                elif url.path == "/users":
                    self.send_json(
                        200, {"users": [service.user], "total": 1, "skip": 0, "limit": 1}
                    )
                elif url.path == f"/users/{service.user['id']}":
                    self.send_json(200, service.user)
                elif url.path == "/carts":
                    self.send_json(
                        200,
                        {
                            "carts": service.carts,
                            "total": len(service.carts),
                            "skip": 0,
                            "limit": len(service.carts),
                        },
                    )
                elif url.path.startswith("/carts/user/"):
                    user_id = int(url.path.split("/")[-1])
                    carts = [c for c in service.carts if c["userId"] == user_id]
                    self.send_json(
                        200, {"carts": carts, "total": len(carts), "skip": 0, "limit": len(carts)}
                    )
                elif url.path == "/unavailable":
                    self.send_json(503, {"message": "Service unavailable"})
                else:
                    self.send_json(404, {"message": "Not found"})

            def do_POST(self) -> None:
                path = urlsplit(self.path).path
                service.requests.append(("POST", path))
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                body = json.loads(raw) if raw else {}
                if path == "/auth/login":
                    if not body.get("username") or not body.get("password"):
                        self.send_json(400, {"message": "Username and password required"})
                        return
                    if (
                        body.get("username") != "demo-user"
                        or body.get("password") != "demo-password"
                    ):
                        self.send_json(400, {"message": "Invalid credentials"})
                        return
                    service.login_count += 1
                    tokens = self.issue_tokens()
                    self.send_json(200, {**service.user, **tokens}, cookie=tokens["accessToken"])
                elif path == "/auth/refresh":
                    if not body.get("refreshToken"):
                        self.send_json(401, {"message": "Refresh token required"})
                        return
                    if body.get("refreshToken") not in service._refresh_tokens:
                        self.send_json(403, {"message": "Invalid refresh token"})
                        return
                    service.refresh_count += 1
                    tokens = self.issue_tokens()
                    self.send_json(200, tokens, cookie=tokens["accessToken"])
                elif path == "/carts/add":
                    if not body.get("userId"):
                        self.send_json(400, {"message": "User id is required"})
                        return
                    if body["userId"] != service.user["id"]:
                        self.send_json(404, {"message": "User not found"})
                        return
                    items = body.get("products", [])
                    if not isinstance(items, list):
                        self.send_json(400, {"message": "products must be array of objects"})
                        return
                    if not items:
                        self.send_json(400, {"message": "products can not be empty"})
                        return
                    # Echo simulated creation, deliberately do not modify service.carts.
                    self.send_json(201, service.make_cart(999, body["userId"], items, created=True))
                else:
                    self.send_json(404, {"message": "Not found"})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = Thread(
            target=lambda: self._server.serve_forever(poll_interval=0.05), daemon=True
        )
        self._thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        assert self._server is not None and self._thread is not None
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
