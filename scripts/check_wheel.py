"""Install the built wheel outside src and exercise packaged contracts and lab routes."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheels = list((root / "dist").glob("*0.5.0*.whl"))
if len(wheels) != 1:
    raise SystemExit("Build exactly one 0.5.0 wheel before running this probe")
probe = """
import json
import os
import socket
import threading
import time
from importlib.resources import files
from pathlib import Path

import api_framework
import framework_lab
import uvicorn
from jsonschema import Draft202012Validator
from playwright.sync_api import sync_playwright
from framework_lab.app import create_app
from framework_lab.delivery import CapturedDelivery
from framework_lab.settings import LabSettings

target = Path(os.environ["WHEEL_PROBE_TARGET"]).resolve()
for package in (api_framework, framework_lab):
    assert Path(package.__file__).resolve().is_relative_to(target)
for asset in ("dummyjson.json", "restful_booker.json", "reqres.json"):
    schema = json.loads(files("api_framework.contracts").joinpath(asset).read_text())
    Draft202012Validator.check_schema(schema)
app = create_app(
    LabSettings("sqlite:///wheel-probe.db", "disposable-wheel-probe-key-" * 2),
    email_delivery=CapturedDelivery(),
)
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
url = f"http://127.0.0.1:{sock.getsockname()[1]}"
server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False))
thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
thread.start()
try:
    deadline = time.monotonic() + 5
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert server.started
    with sync_playwright() as driver:
        context = driver.request.new_context(base_url=url, timeout=5000)
        try:
            assert context.get("/health").json() == {"status": "ready"}
            response = context.post("/auth/register", data={
                "email": "wheel@example.test", "password": "synthetic-wheel-password",
                "mfa_method": "email",
            })
            assert response.status == 201
            assert context.get("/auth/me").status == 401
        finally:
            context.dispose()
finally:
    server.should_exit = True
    thread.join(timeout=5)
    sock.close()
    app.state.engine.dispose()
    assert not thread.is_alive()
print("Installed wheel: both packages, three schema assets, health/register/auth rejection passed")
"""
with tempfile.TemporaryDirectory(prefix="phase5-wheel-") as directory:
    target = Path(directory) / "installed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(target),
            str(wheels[0]),
        ],
        check=True,
    )
    environment = {**os.environ, "PYTHONPATH": str(target), "WHEEL_PROBE_TARGET": str(target)}
    subprocess.run([sys.executable, "-c", probe], cwd=directory, env=environment, check=True)
