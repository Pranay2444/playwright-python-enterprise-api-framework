"""Minimal local ReqRes wiring model; not a provider contract oracle."""

import json
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4


class LocalReqRes:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.requests: list[tuple[str, str]] = []
        self.forced_status: dict[tuple[str, str], int] = {}
        self.invalid_created_metadata = False
        self.accept_unwrapped_create = False
        self.users = [
            {
                "id": value,
                "email": f"qa{value}@example.test",
                "first_name": "QA",
                "last_name": f"User{value}",
                "avatar": f"https://example.test/{value}.jpg",
            }
            for value in [71, 82, 93]
        ]
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def base_url(self) -> str:
        assert self._server is not None
        return f"http://127.0.0.1:{self._server.server_port}"

    def __enter__(self) -> "LocalReqRes":
        service = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def send(self, status: int, body: Any = None) -> None:
                encoded = b"" if status == 204 else json.dumps(body).encode()
                self.send_response(status)
                if status != 204:
                    self.send_header("Content-Type", "application/json")
                if status == 429:
                    self.send_header("Retry-After", "30")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def body(self) -> dict[str, Any]:
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                return json.loads(raw) if raw else {}

            def route(self, method: str) -> None:
                url = urlsplit(self.path)
                query = parse_qs(url.query)
                service.requests.append((method, url.path))
                forced = service.forced_status.get((method, url.path))
                if forced:
                    self.send(forced, {"error": "Injected failure"})
                    return
                if url.path == "/api/users":
                    if method == "POST":
                        self.send(
                            201,
                            {
                                **self.body(),
                                "id": "simulated-1",
                                "createdAt": "2030-01-01T00:00:00Z",
                            },
                        )
                    elif method == "GET":
                        page = int(query.get("page", ["1"])[0])
                        size = int(query.get("per_page", ["2"])[0])
                        start = (page - 1) * size
                        self.send(
                            200,
                            {
                                "page": page,
                                "per_page": size,
                                "total": len(service.users),
                                "total_pages": (len(service.users) + size - 1) // size,
                                "data": service.users[start : start + size],
                            },
                        )
                    else:
                        self.send(404, {})
                    return
                if url.path.startswith("/api/users/") and method == "GET":
                    found = next(
                        (u for u in service.users if str(u["id"]) == url.path.split("/")[-1]), None
                    )
                    self.send(200 if found else 404, {"data": found} if found else {})
                    return
                root = "/api/collections/products/records"
                if url.path != root and not url.path.startswith(root + "/"):
                    self.send(404, {"error": "Not found"})
                    return
                if self.headers.get("x-api-key") != "local-manage-key":
                    self.send(401, {"error": "Unauthorized"})
                    return
                if query.get("project_id") != ["local-project"]:
                    self.send(404, {"error": "Unknown project"})
                    return
                if self.headers.get("X-Reqres-Env") != "prod":
                    self.send(400, {"error": "Unknown environment"})
                    return
                record_id = url.path.removeprefix(root + "/") if url.path != root else None
                if method == "GET":
                    if record_id is None:
                        search = query.get("search", [""])[0].lower()
                        limit = int(query.get("limit", ["10"])[0])
                        records = [
                            r
                            for r in service.records.values()
                            if search in json.dumps(r["data"]).lower()
                        ]
                        self.send(200, {"data": records[:limit]})
                    elif record_id in service.records:
                        self.send(200, {"data": service.records[record_id]})
                    else:
                        self.send(404, {"error": "Not found"})
                elif method in {"POST", "PUT"}:
                    body = self.body()
                    if method == "POST" and service.accept_unwrapped_create:
                        body = {"data": body}
                    if not isinstance(body.get("data"), dict):
                        self.send(400, {"error": "Missing data wrapper"})
                        return
                    if method == "POST" and record_id is None:
                        record_id = str(uuid4())
                        record = {
                            "id": record_id,
                            "data": deepcopy(body["data"]),
                            "created_at": "2030-01-01T00:00:00Z",
                        }
                        if service.invalid_created_metadata:
                            record["created_at"] = 42
                        service.records[record_id] = record
                        self.send(201, {"data": record})
                    elif method == "PUT" and record_id in service.records:
                        service.records[record_id]["data"] = deepcopy(body["data"])
                        self.send(200, {"data": service.records[record_id]})
                    else:
                        self.send(404, {"error": "Not found"})
                elif method == "DELETE" and record_id in service.records:
                    del service.records[record_id]
                    self.send(204)
                else:
                    self.send(404, {"error": "Not found"})

            def do_GET(self) -> None:
                self.route("GET")

            def do_POST(self) -> None:
                self.route("POST")

            def do_PUT(self) -> None:
                self.route("PUT")

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
