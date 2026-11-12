"""The people who sign in. Each one has a folder of their own under data/people, with their own database,
portraits and backgrounds, so nobody sees anybody else's stories or connections.

Until the first person is added, Bamah has one password (BAMAH_PASSWORD) and uses the data folder as it is.
The first person starts with a copy of it and invites the others by email (mail.py). A new person starts
with a copy of everything of whoever invited them, or with only their models, settings and portrait library.

Signing in takes a name or an email, then a six-digit code by email or, for anyone who set one, a password.
- A code works for 10 minutes and 5 tries.
- Codes: 6 per IP address an hour, 3 to one address every 15 minutes and 8 a day, 100 an hour in all.
- 20 wrong codes from one IP address in an hour, and it waits.
- Passwords: 12 tries from one IP address in 15 minutes, and 8 wrong for one person locks it for 15.
- Invites: 3 a day to one person.
A new password, or removing someone, signs them out everywhere else: `gen`, which the cookie carries, goes up.

  docker exec bamah python -m bamah.people list
  docker exec bamah python -m bamah.people email NAME ADDRESS     (their email, from the server)
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sys
import threading
import time
from pathlib import Path

from . import config, db, emails, mail

FILE = "people.json"
CODE_SECONDS = 600
CODE_TRIES = 5
PASSWORD_MIN = 8
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")

_lock = threading.Lock()
_codes: dict[int, dict] = {}            # person id -> {hash, exp, tries}, in memory only
_hits: dict[str, list[float]] = {}


class Refused(Exception):
    """A short reason the page turns into a message: name, taken, email, exists, short, long, current,
    not-found, no-email, mail, throttled, locked, wrong, expired, login."""


# --- The list ---------------------------------------------------------------------------------

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


def clean_email(s) -> str:
    return str(s or "").strip().lower()


def find(who: str, every: list[dict] | None = None) -> dict | None:
    """Someone by their email, or by their name in any case."""
    who = str(who or "").strip()
    every = load() if every is None else every
    if "@" in who:
        return next((p for p in every if p.get("email") and p["email"] == clean_email(who)), None)
    return next((p for p in every if who and p["name"].casefold() == who.casefold()), None)


def public(p: dict) -> dict:
    return {"id": p["id"], "name": p["name"], "email": p.get("email"), "admin": bool(p.get("admin")),
            "joined": bool(p.get("joined", True)), "password": bool(p.get("password"))}   # no key: from before invites


def mask(email: str) -> str:
    name, _, domain = email.partition("@")
    return f"{name[:1]}•••@{domain}"


def _name(name, every, but=None) -> str:
    name = re.sub(r"\s+", " ", str(name or "")).strip()
    if not name or len(name) > 40 or "@" in name:
        raise Refused("name")
    if any(p is not but and p["name"].casefold() == name.casefold() for p in every):
        raise Refused("taken")
    return name


def _email(email, every, but=None) -> str | None:
    email = clean_email(email)
    if not email:
        return None
    if not EMAIL.match(email):
        raise Refused("email")
    if any(p is not but and p.get("email") == email for p in every):
        raise Refused("exists")
    return email


# --- Passwords: scrypt, with its salt ---------------------------------------------------------

def _hash(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    h = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1, dklen=32).hex()
    return f"scrypt${salt}${h}"


def check(person: dict | None, password: str) -> bool:
    try:
        _, salt, want = (person or {})["password"].split("$")
    except (KeyError, AttributeError, ValueError):
        _hash("x")                         # the same time whether or not there's a password
        return False
    return hmac.compare_digest(_hash(password, salt).rpartition("$")[2], want)


def _good(password: str) -> str:
    if len(password) < PASSWORD_MIN:
        raise Refused("short")
    if len(password) > 200:
        raise Refused("long")
    return password


# --- Adding, changing and removing people -----------------------------------------------------

def add(name: str, email: str | None, copy_from: Path, stories: bool = True, password: str | None = None) -> dict:
    """A new person, with a copy of the folder given: everything, or without the stories and characters.
    Everyone needs an email or a password to sign in with: an email where mail can go out, else a password."""
    with _lock:
        people = load()
        name, email = _name(name, people), _email(email, people)
        password = _good(password) if password else None
        if not email and not password:
            raise Refused("email")             # nothing to sign in with
        pid = max((p["id"] for p in people), default=0) + 1
        dest = folder(pid)
        if dest.exists():          # a folder left by a removal that never finished; put it out of the way
            dest.rename(dest.with_name(f"{pid}-old-{int(time.time())}"))
        dest.mkdir(parents=True)
        _copy(copy_from, dest, stories)
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        person = {"id": pid, "name": name, "email": email, "password": _hash(password) if password else None,
                  "admin": not people, "gen": 0, "added": now, "joined": now if not people else None}
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
            d.execute("delete from portrait where coalesce(source, '') = ''")   # theirs; the library stays
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


def _change(pid: int, fn) -> dict:
    with _lock:
        people = load()
        p = next((p for p in people if p["id"] == pid), None)
        if not p:
            raise Refused("not-found")
        fn(p, people)
        _save(people)
    return p


def edit(pid: int, name: str | None = None, email: str | None = None) -> dict:
    def do(p, people):
        if name is not None:
            p["name"] = _name(name, people, but=p)
        if email is not None:
            e = _email(email, people, but=p)
            if not e and not p.get("password"):
                raise Refused("email")         # nothing left to sign in with
            if e != p.get("email"):
                _codes.pop(pid, None)
            p["email"] = e
    return _change(pid, do)


def set_password(pid: int, new: str, current: str | None = None) -> dict:
    """A new password, which signs that person out everywhere else."""
    _good(str(new or ""))
    p = get(pid)
    if p and p.get("password") and not check(p, str(current or "")):
        raise Refused("current")
    stored = _hash(new)

    def do(p, _):
        p["password"], p["gen"] = stored, p.get("gen", 0) + 1
    return _change(pid, do)


def remove_password(pid: int, current: str | None) -> dict:
    p = get(pid)
    if p and p.get("password") and not check(p, str(current or "")):
        raise Refused("current")

    def do(p, _):
        if not p.get("email"):
            raise Refused("email")
        p["password"] = None
    return _change(pid, do)


def remove(pid: int):
    """Out of the list, and their folder put aside under data/removed rather than deleted."""
    with _lock:
        people = load()
        _save([p for p in people if p["id"] != pid])
        f = folder(pid)
        if f.exists():
            config.root("removed", "x")
            f.rename(config.DATA / "removed" / f"{pid}-{int(time.time())}")
    _codes.pop(pid, None)


def invite(p: dict, inviter: dict | None, stories: bool = True) -> bool:
    """The email that tells them they're in. True when it went out."""
    with _lock:
        if _limited(f"invite:{p['id']}", 3, 86400):
            raise Refused("throttled")
        _hit(f"invite:{p['id']}")
    return mail.send(p["email"], *emails.invite(name=p["name"], email=p["email"], url=config.URL, stories=stories,
                                                 signature=config.SIGNATURE or (inviter or {}).get("name", "")))


# --- Signing in -------------------------------------------------------------------------------

def _limited(key: str, most: int, seconds: float) -> bool:
    now = time.time()
    _hits[key] = [t for t in _hits.get(key, []) if now - t < seconds]
    return len(_hits[key]) >= most


def _hit(*keys: str):
    now = time.time()
    for k in keys:
        _hits.setdefault(k, []).append(now)


def _sha(pid: int, code: str) -> str:
    return hashlib.sha256(f"{pid}:{code}".encode()).hexdigest()


def send_code(who: str, ip: str) -> dict:
    """Email a code to whoever `who` is, a name or an email. Returns where it went, masked."""
    with _lock:
        if _limited(f"ip:{ip}", 6, 3600) or _limited("all", 100, 3600):
            raise Refused("throttled")
        _hit(f"ip:{ip}", "all")            # names that aren't there count too, so nobody can fish for them
        p = find(who)
        if not p:
            raise Refused("not-found")
        if not p.get("email"):
            raise Refused("no-email")
        if _limited(f"to:{p['id']}", 3, 900) or _limited(f"day:{p['id']}", 8, 86400):
            raise Refused("throttled")
        _hit(f"to:{p['id']}", f"day:{p['id']}")
        code = f"{secrets.randbelow(10 ** 6):06d}"
        _codes[p["id"]] = {"hash": _sha(p["id"], code), "exp": time.time() + CODE_SECONDS, "tries": 0}
    if not mail.send(p["email"], *emails.code(code, config.URL, CODE_SECONDS // 60)):
        _codes.pop(p["id"], None)
        raise Refused("mail")
    return {"to": mask(p["email"])}


def _joined(pid: int) -> dict:
    def do(p, _):
        p["joined"] = p.get("joined") or time.strftime("%Y-%m-%d %H:%M:%S")
    return _change(pid, do)


def sign_in_code(who: str, code: str, ip: str) -> dict:
    with _lock:
        if _limited(f"bad:{ip}", 20, 3600):
            raise Refused("throttled")
        p = find(who)
        c = _codes.get(p["id"]) if p else None
        if not c or c["exp"] < time.time():
            raise Refused("expired")
        if not hmac.compare_digest(c["hash"], _sha(p["id"], re.sub(r"\D", "", str(code or "")))):
            _hit(f"bad:{ip}")
            c["tries"] += 1
            if c["tries"] >= CODE_TRIES:
                _codes.pop(p["id"], None)
            raise Refused("wrong")
        _codes.pop(p["id"], None)
    return _joined(p["id"])


def sign_in_password(who: str, password: str, ip: str) -> dict:
    who, password = str(who or "").strip()[:254], str(password or "")[:200]
    if not who or not password:
        raise Refused("login")
    with _lock:
        if _limited(f"pw-ip:{ip}", 12, 900):
            raise Refused("throttled")
        _hit(f"pw-ip:{ip}")
        p = find(who)
        if p and _limited(f"pw:{p['id']}", 8, 900):
            raise Refused("locked")
    if not check(p, password) or not p:
        if p:
            with _lock:
                _hit(f"pw:{p['id']}")
        raise Refused("login")
    _hits.pop(f"pw:{p['id']}", None)
    return _joined(p["id"])


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0] if argv else "list"), argv[1:]
    try:
        if cmd == "list":
            for p in load():
                print(f"{p['id']:>3}  {p['name']:<24} {p.get('email') or '-':<36} "
                      f"{'admin ' if p.get('admin') else ''}{'password ' if p.get('password') else ''}"
                      f"{'' if p.get('joined', True) else 'invited'}")
        elif cmd == "email" and len(rest) == 2:
            p = find(rest[0])
            if not p:
                raise Refused("not-found")
            edit(p["id"], email=rest[1])
            print("Saved.")
        else:
            print(__doc__.split("\n\n")[-1])
            return 2
    except Refused as e:
        print(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
