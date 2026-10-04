"""Generate a private local signing key without displaying or overwriting it."""

import os
import secrets
from pathlib import Path

folder = Path(__file__).resolve().parents[1] / "lab" / ".secrets"
folder.mkdir(parents=True, exist_ok=True, mode=0o700)
path = folder / "signing-key"
if not path.exists():
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(secrets.token_urlsafe(48))
print("Lab signing key is ready; its value is never displayed")
