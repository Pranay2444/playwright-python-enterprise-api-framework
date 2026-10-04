"""Small persistent HTTP model for adapter/cleanup checks, not a provider oracle."""

import json
from copy import deepcopy
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlsplit


class LocalBooker:
    def __init__(self) -> None:
        self.bookings: dict[int, dict[str, Any]] = {}
        self.requests: list[tuple[str, str]] = []
        self.next_id = 601
        self.tokens: set[str] = set()
        self.delete_failures: dict[int, int] = {}
        self.invalid_created_booking = False
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def base_url(self) -> str:
        assert self._server is not None
        return f"http://127.0.0.1:{self._server.server_port}"

    def __enter__(self) -> "LocalBooker":
        service = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def send_body(self, status: int, body: Any, *, as_json: bool = True) -> None:
                encoded = (json.dumps(body) if as_json else body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json" if as_json else "text/plain")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def read_body(self) -> dict[str, Any]:
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                return json.loads(raw) if raw else {}

            def route(self, method: str) -> None:
                url = urlsplit(self.path)
                service.requests.append((method, url.path))
                if method == "GET" and url.path == "/ping":
                    self.send_body(201, "Created", as_json=False)
                    return
                if method == "POST" and url.path == "/auth":
                    body = self.read_body()
                    if (
                        body.get("username") == "local-admin"
                        and body.get("password") == "local-password"
                    ):
                        token = f"local-booker-{len(service.tokens) + 1}"
                        service.tokens.add(token)
                        self.send_body(200, {"token": token})
                    else:
                        self.send_body(200, {"reason": "Bad credentials"})
                    return
                if url.path == "/booking":
                    if method == "GET":
                        query = parse_qs(url.query)
                        ids = [
                            {"bookingid": booking_id}
                            for booking_id, body in service.bookings.items()
                            if all(body.get(key) == values[0] for key, values in query.items())
                        ]
                        self.send_body(200, ids)
                    elif method == "POST":
                        body = self.read_body()
                        booking_id = service.next_id
                        service.next_id += 1
                        service.bookings[booking_id] = deepcopy(body)
                        returned = deepcopy(body)
                        if service.invalid_created_booking:
                            returned.pop("depositpaid", None)
                            service.bookings[booking_id].pop("depositpaid", None)
                        self.send_body(200, {"bookingid": booking_id, "booking": returned})
                    else:
                        self.send_body(404, "Not Found", as_json=False)
                    return
                if not url.path.startswith("/booking/"):
                    self.send_body(404, "Not Found", as_json=False)
                    return
                try:
                    booking_id = int(url.path.split("/")[-1])
                except ValueError:
                    self.send_body(404, "Not Found", as_json=False)
                    return
                if method == "GET":
                    if booking_id in service.bookings:
                        self.send_body(200, service.bookings[booking_id])
                    else:
                        self.send_body(404, "Not Found", as_json=False)
                    return
                cookie = SimpleCookie()
                cookie.load(self.headers.get("Cookie", ""))
                token = cookie.get("token")
                if token is None or token.value not in service.tokens:
                    self.send_body(403, "Forbidden", as_json=False)
                    return
                if booking_id not in service.bookings:
                    self.send_body(405, "Method Not Allowed", as_json=False)
                    return
                if method in {"PUT", "PATCH"}:
                    body = self.read_body()
                    if method == "PUT":
                        service.bookings[booking_id] = deepcopy(body)
                    else:
                        service.bookings[booking_id].update(deepcopy(body))
                    self.send_body(200, service.bookings[booking_id])
                elif method == "DELETE":
                    if booking_id in service.delete_failures:
                        self.send_body(
                            service.delete_failures[booking_id], "Delete failed", as_json=False
                        )
                    else:
                        del service.bookings[booking_id]
                        self.send_body(201, "Created", as_json=False)
                else:
                    self.send_body(404, "Not Found", as_json=False)

            def do_GET(self) -> None:
                self.route("GET")

            def do_POST(self) -> None:
                self.route("POST")

            def do_PUT(self) -> None:
                self.route("PUT")

            def do_PATCH(self) -> None:
                self.route("PATCH")

            def do_DELETE(self) -> None:
                self.route("DELETE")

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
