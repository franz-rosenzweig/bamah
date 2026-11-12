"""The people who sign in. Each one has a folder of their own under data/people, with their own database,
portraits and backgrounds, so nobody sees anybody else's stories or connections.

Until the first person is added, Bamah has one password (BAMAH_PASSWORD) and uses the data folder as it is.
The first person starts with a copy of it and can add the others; a new person starts with a copy of
everything of whoever added them, or only their connections, settings and portrait library."""

import hashlib
import hmac
import json
import os
import shutil
import threading
import time
from pathlib import Path

from . import config, db

FILE = "people.json"
_lock = threading.Lock()


def load() -> list[dict]:
    f = config.DATA / FILE
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text())
    except ValueError:
        return []


def _save(people: list[dict]):
    f = config.root(FILE)
    tmp = f.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as out:
        json.dump(people, out, indent=1)
    os.replace(tmp, f)


def folder(pid: int) -> Path:
    return config.DATA / "people" / str(pid)


def get(pid) -> dict | None:
    return next((p for p in load() if p["id"] == pid), None)


def named(name: str) -> dict | None:
    name = name.strip().casefold()
    return next((p for p in load() if p["name"].casefold() == name), None)


def public(p: dict) -> dict:
    return {"id": p["id"], "name": p["name"], "admin": bool(p.get("admin"))}


def _hash(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    h = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1, dklen=32).hex()
    return f"scrypt${salt}${h}"


def check(person: dict, password: str) -> bool:
    try:
        _, salt, want = person["password"].split("$")
    except ValueError:
        return False
    return hmac.compare_digest(_hash(password, salt).rpartition("$")[2], want)


def add(name: str, password: str, copy_from: Path, stories: bool = True) -> dict:
    """A new person, with a copy of the folder given: everything, or without the stories and characters."""
    with _lock:
        people = load()
        pid = max((p["id"] for p in people), default=0) + 1
        dest = folder(pid)
        if dest.exists():          # a folder left by a removal that never finished; put it out of the way
            dest.rename(dest.with_name(f"{pid}-old-{int(time.time())}"))
        dest.mkdir(parents=True)
        _copy(copy_from, dest, stories)
        person = {"id": pid, "name": name.strip(), "password": _hash(password), "admin": not people, "gen": 0,
                  "added": time.strftime("%Y-%m-%d %H:%M:%S")}
        people.append(person)
        _save(people)
    return person


def _copy(src: Path, dest: Path, stories: bool):
    db.init(src)
    a, b = db.connect(src), db.connect(dest)
    try:
        a.backup(b)
    finally:
        a.close()
        b.close()
    db.init(dest)
    if not stories:
        with db.connect(dest) as d:
            for table in ("story", "character", "persona", "journal"):
                d.execute(f"delete from {table}")
            d.execute("delete from portrait where coalesce(source, '') = ''")   # hers; the library stays
    with db.connect(dest) as d:
        keep = {r[0] for r in d.execute("select file from portrait")} | \
               {r[0] for r in d.execute("select avatar from character where avatar is not null")} | \
               {r[0] for r in d.execute("select background from scene where background != ''")}
    # the same pictures, linked rather than copied: a picture is never changed, only added or deleted
    for sub in ("avatars", "backgrounds"):
        if not (src / sub).is_dir():
            continue
        (dest / sub).mkdir(exist_ok=True)
        for f in (src / sub).iterdir():
            if f.is_file() and (stories or f.name in keep):
                try:
                    os.link(f, dest / sub / f.name)
                except OSError:
                    shutil.copy2(f, dest / sub / f.name)


def set_password(pid: int, password: str) -> dict:
    """A new password, which signs that person out everywhere else."""
    with _lock:
        people = load()
        p = next(p for p in people if p["id"] == pid)
        p["password"] = _hash(password)
        p["gen"] = p.get("gen", 0) + 1
        _save(people)
    return p


def remove(pid: int):
    """Out of the list, and their folder put aside under data/removed rather than deleted."""
    with _lock:
        people = load()
        _save([p for p in people if p["id"] != pid])
        f = folder(pid)
        if f.exists():
            config.root("removed", "x")
            f.rename(config.DATA / "removed" / f"{pid}-{int(time.time())}")
