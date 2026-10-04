"""Read the Compose secret at bootstrap, then run the application as UID 10001."""

import os
import sys
from pathlib import Path

os.environ["LAB_SIGNING_KEY"] = Path(os.environ.pop("LAB_SIGNING_KEY_FILE")).read_text().strip()
os.setgroups([])
os.setgid(10001)
os.setuid(10001)
os.execv(
    sys.executable,
    [
        sys.executable,
        "-m",
        "uvicorn",
        "framework_lab.app:create_app",
        "--factory",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--no-access-log",
    ],
)
