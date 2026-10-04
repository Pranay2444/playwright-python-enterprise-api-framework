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
            {"id": 731, "title": "Demo Hammer", "price": 12.5},
            {"id": 947, "title": "Demo Drill", "price": 40.0},
        ]
        self.user = {"id": 503, "username": "demo-user", "firstName": "Demo"}
        self.carts = [{"id": 811, "userId": 503, "products": [self.products[0]]}]
        self.requests: list[tuple[str, str]] = []
        self.login_count = 0
        self.refresh_count = 0
        self._access_tokens: set[str] = set()
        self._refresh_tokens: set[str] = set()
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

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
                    self.send_json(200 if allowed else 401, service.user if allowed else {})
                elif url.path in {"/products", "/products/search"}:
                    products = service.products
                    if url.path.endswith("search"):
                        term = query.get("q", [""])[0].casefold()
                        products = [p for p in products if term in p["title"].casefold()]
                    skip = int(query.get("skip", ["0"])[0])
                    limit = int(query.get("limit", [str(len(products))])[0])
                    selected = products[skip : skip + limit]
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
                    self.send_json(200, {"carts": service.carts, "total": len(service.carts)})
                elif url.path.startswith("/carts/user/"):
                    user_id = int(url.path.split("/")[-1])
                    carts = [c for c in service.carts if c["userId"] == user_id]
                    self.send_json(200, {"carts": carts, "total": len(carts)})
                elif url.path == "/unavailable":
                    self.send_json(503, {"message": "Service unavailable"})
                else:
                    self.send_json(404, {"message": "Not found"})

            def do_POST(self) -> None:
                path = urlsplit(self.path).path
                service.requests.append(("POST", path))
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                if path == "/auth/login":
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
                    if body.get("refreshToken") not in service._refresh_tokens:
                        self.send_json(401, {"message": "Invalid refresh token"})
                        return
                    service.refresh_count += 1
                    tokens = self.issue_tokens()
                    self.send_json(200, tokens, cookie=tokens["accessToken"])
                elif path == "/carts/add":
                    products = []
                    for item in body["products"]:
                        product = next(p for p in service.products if p["id"] == item["id"])
                        products.append({**product, "quantity": item["quantity"]})
                    # Echo simulated creation, deliberately do not modify service.carts.
                    self.send_json(
                        201,
                        {
                            "id": 999,
                            "userId": body["userId"],
                            "products": products,
                            "totalProducts": len(products),
                            "totalQuantity": sum(p["quantity"] for p in products),
                        },
                    )
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
