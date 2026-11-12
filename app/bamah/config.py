"""Settings that come from the environment (see .env.example)."""

import contextvars
import os
import secrets
from pathlib import Path

DATA = Path(os.environ.get("BAMAH_DATA", "./data")).resolve()
PASSWORD = os.environ.get("BAMAH_PASSWORD", "")      # empty: no sign-in (a copy on your own computer)
PORT = int(os.environ.get("BAMAH_PORT", "8465"))     # the port the browser opens; ChatGPT's sign-in returns to it
NAME = os.environ.get("BAMAH_NAME", "Bamah")


# The folder of whoever is signed in (people.py), set for each request; until there are people, the data folder itself.
HOME: contextvars.ContextVar[Path | None] = contextvars.ContextVar("home", default=None)


def home() -> Path:
    return HOME.get() or DATA


def path(*parts) -> Path:
    """A file of the person signed in: their database, portraits and backgrounds."""
    p = home().joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def root(*parts) -> Path:
    """A file of the whole server, whoever is signed in."""
    p = DATA.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def secret() -> bytes:
    """The key that signs the sign-in cookie, made once and kept with the data."""
    f = root("secret")
    if not f.exists():
        f.write_text(secrets.token_hex(32))
        f.chmod(0o600)
    return f.read_text().strip().encode()
