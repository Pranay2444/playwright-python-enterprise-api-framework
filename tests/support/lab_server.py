"""A real Uvicorn HTTP target, with disposable DB ownership per test/worker."""

import socket
import threading
import time

import uvicorn


class LabServer:
    def __init__(self, app):
        self.socket = socket.socket()
        self.socket.bind(("127.0.0.1", 0))
        self.base_url = f"http://127.0.0.1:{self.socket.getsockname()[1]}"
        self.server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level="critical"))
        self.thread = threading.Thread(
            target=self.server.run, kwargs={"sockets": [self.socket]}, daemon=True
        )

    def __enter__(self):
        self.thread.start()
        deadline = time.monotonic() + 5
        while not self.server.started:
            if not self.thread.is_alive() or time.monotonic() >= deadline:
                self.server.should_exit = True
                self.thread.join(timeout=5)
                self.socket.close()
                raise RuntimeError("Owned lab did not start before the readiness deadline")
            time.sleep(0.01)
        return self

    def __exit__(self, *_args):
        self.server.should_exit = True
        self.thread.join(timeout=5)
        self.socket.close()
        if self.thread.is_alive():
            raise RuntimeError("Owned lab did not stop before the shutdown deadline")
