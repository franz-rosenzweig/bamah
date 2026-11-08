"""Settings that come from the environment (see .env.example)."""

import os
import secrets
from pathlib import Path

DATA = Path(os.environ.get("BAMAH_DATA", "./data")).resolve()
PASSWORD = os.environ.get("BAMAH_PASSWORD", "")      # empty: no sign-in (a copy on your own computer)
PORT = int(os.environ.get("BAMAH_PORT", "8465"))     # the port the browser opens; ChatGPT's sign-in returns to it
NAME = os.environ.get("BAMAH_NAME", "Bamah")


def path(*parts) -> Path:
    p = DATA.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def secret() -> bytes:
    """The key that signs the sign-in cookie, made once and kept with the data."""
    f = path("secret")
    if not f.exists():
        f.write_text(secrets.token_hex(32))
        f.chmod(0o600)
    return f.read_text().strip().encode()
