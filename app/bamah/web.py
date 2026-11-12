"""The web app: a JSON API for the page, and the page itself."""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse, StreamingResponse

from . import chatgpt, config, db, docs, engine, images, mail, models, people

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("bamah.web")

STATIC = Path(__file__).parent / "static"
COOKIE = "bamah"
OPEN = ("/login", "/api/login", "/static/app.css", "/static/themes.js", "/static/icon.svg", "/static/icon-180.png",
        "/static/icon-192.png", "/static/icon-512.png", "/manifest.webmanifest", "/fonts/")

@asynccontextmanager
async def _life(_app):
    db.init()
    for p in people.load():
        db.init(people.folder(p["id"]))
    yield


app = FastAPI(title=config.NAME, docs_url=None, redoc_url=None, openapi_url=None, lifespan=_life)


# --- Signing in -------------------------------------------------------------------------------
# Before there are people (people.py) there's one password, BAMAH_PASSWORD, or none at all on your own
# computer. Once there are, each signs in with their name and password, and every request reads and
# writes their folder alone.

def _sign(value: str) -> str:
    return hmac.new(config.secret(), value.encode(), hashlib.sha256).hexdigest()


def _cookie(request: Request) -> str | None:
    value, _, mac = request.cookies.get(COOKIE, "").rpartition(".")
    return value if value and hmac.compare_digest(_sign(value), mac) else None


def _person(request: Request) -> dict | None:
    """Who the cookie says is signed in: p<id>-<gen>-…, and gen goes up when their password changes."""
    value = _cookie(request) or ""
    if not value.startswith("p"):
        return None
    try:
        pid, gen, _ = value[1:].split("-", 2)
        p = people.get(int(pid))
    except ValueError:
        return None
    return p if p and str(p.get("gen", 0)) == gen else None


def _signed_in(request: Request) -> bool:
    return not config.PASSWORD or _cookie(request) is not None


@app.middleware("http")
async def _gate(request: Request, call_next):
    path = request.url.path
    if people.load():
        p = _person(request)
        if p:
            config.HOME.set(people.folder(p["id"]))
        elif not path.startswith(OPEN):
            return _out(path)
    elif config.PASSWORD and not path.startswith(OPEN) and not _signed_in(request):
        return _out(path)
    return await call_next(request)


def _out(path: str):
    if path.startswith("/api/"):
        return JSONResponse({"error": "signin"}, status_code=401)
    return RedirectResponse("/login")


def _sign_in(request: Request, r: JSONResponse, person: dict | None = None) -> JSONResponse:
    value = f"{int(time.time())}-{secrets.token_hex(8)}"
    if person:
        value = f"p{person['id']}-{person.get('gen', 0)}-{value}"
    r.set_cookie(COOKIE, f"{value}.{_sign(value)}", max_age=60 * 60 * 24 * 400, httponly=True, samesite="lax",
                 secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https")
    return r


def _client(request: Request) -> str:
    return (request.headers.get("cf-connecting-ip")
            or (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            or (request.client.host if request.client else "?"))


STATUS = {"throttled": 429, "locked": 429, "mail": 502, "wrong": 401, "expired": 401, "login": 401, "current": 401,
          "not-found": 404, "taken": 409, "exists": 409}


async def _do(fn, *a, **kw):
    """people.py's work, off the event loop (scrypt and SMTP both take a moment), its refusals as errors."""
    try:
        return await asyncio.to_thread(fn, *a, **kw)
    except people.Refused as e:
        raise HTTPException(STATUS.get(str(e), 400), str(e))


@app.get("/login")
def login_page():
    return FileResponse(STATIC / "login.html")


@app.get("/api/login")
def login_form():
    return {"names": bool(people.load()), "mail": mail.available()}


@app.post("/api/login")
async def login(request: Request):
    """A password: the shared one until there are people, then each person's own."""
    body = await _body(request)
    password = str(body.get("password", ""))
    if people.load():
        p = await _do(people.sign_in_password, str(body.get("name", "")), password, _client(request))
        return _sign_in(request, JSONResponse({"ok": True}), p)
    if config.PASSWORD and hmac.compare_digest(password.encode(), config.PASSWORD.encode()):
        return _sign_in(request, JSONResponse({"ok": True}))
    await asyncio.sleep(1)
    raise HTTPException(401, "login")


@app.post("/api/login/code")
async def login_code(request: Request):
    body = await _body(request)
    return await _do(people.send_code, str(body.get("who", "")), _client(request))


@app.post("/api/login/verify")
async def login_verify(request: Request):
    body = await _body(request)
    p = await _do(people.sign_in_code, str(body.get("who", "")), str(body.get("code", "")), _client(request))
    return _sign_in(request, JSONResponse({"ok": True}), p)


@app.post("/api/logout")
def logout():
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE)
    return r


# --- People -----------------------------------------------------------------------------------

def _admin(request: Request) -> dict:
    me = _person(request)
    if not me or not me.get("admin"):
        raise HTTPException(403, "admin")
    return me


@app.get("/api/people")
def people_list(request: Request):
    every = people.load()
    if not every:
        return {"on": False, "me": None, "people": [], "mail": mail.available()}
    me = _person(request)
    return {"on": True, "me": people.public(me), "mail": mail.available(),
            "people": [people.public(p) for p in every] if me.get("admin") else [people.public(me)]}


@app.post("/api/people")
async def add_person(request: Request):
    """The first person is whoever sets it up, with everything that's here; after that, the first
    invites the others by email."""
    body = await _body(request)
    first = not people.load()
    me = None if first else _admin(request)
    stories = first or bool(body.get("stories", True))
    p = await _do(people.add, str(body.get("name", "")), str(body.get("email", "")), config.home(), stories,
                  str(body.get("password") or "") or None)
    if first:
        return _sign_in(request, JSONResponse({"person": people.public(p), "invited": False}), p)
    invited = await _do(people.invite, p, me, stories)
    return {"person": people.public(p), "invited": invited}


@app.patch("/api/people/{pid}")
async def edit_person(pid: int, request: Request):
    """A name or an email: your own, or anyone's for the first person."""
    me = _person(request)
    if not me or (me["id"] != pid and not me.get("admin")):
        raise HTTPException(403, "admin")
    body = await _body(request)
    p = await _do(people.edit, pid, name=body.get("name"), email=body.get("email"))
    return people.public(p)


@app.post("/api/people/{pid}/invite")
async def invite_again(pid: int, request: Request):
    me = _admin(request)
    p = people.get(pid)
    if not p or not p.get("email"):
        raise HTTPException(404, "not-found")
    if not await _do(people.invite, p, me):
        raise HTTPException(502, "mail")
    return {"invited": True}


@app.delete("/api/people/{pid}")
def remove_person(pid: int, request: Request):
    me = _admin(request)
    if me["id"] == pid:
        raise HTTPException(403, "admin")
    if not people.get(pid):
        raise HTTPException(404, "not-found")
    people.remove(pid)
    return {"ok": True}


@app.put("/api/me/password")
async def my_password(request: Request):
    """Your own password, which signs you out everywhere else."""
    me = _person(request)
    if not me:
        raise HTTPException(403, "admin")
    body = await _body(request)
    p = await _do(people.set_password, me["id"], str(body.get("password", "")), body.get("current"))
    return _sign_in(request, JSONResponse({"ok": True}), p)


@app.delete("/api/me/password")
async def my_password_off(request: Request):
    me = _person(request)
    if not me:
        raise HTTPException(403, "admin")
    body = await _body(request)
    await _do(people.remove_password, me["id"], body.get("current"))
    return {"ok": True}


# --- Helpers ----------------------------------------------------------------------------------

async def _body(request: Request) -> dict:
    try:
        return await request.json()
    except ValueError:
        return {}


def _one(d, sql, args=()):
    r = db.row(d.execute(sql, args).fetchone())
    if r is None:
        raise HTTPException(404, "not found")
    return r


def _update(d, table: str, rid: int, body: dict, fields: tuple):
    sets, args = [], []
    for f in fields:
        if f in body:
            v = body[f]
            if isinstance(v, (list, dict)):
                v = json.dumps(v)
            sets.append(f"{f} = ?")
            args.append(v)
    if sets:
        if table in ("character", "story"):
            sets.append("updated_at = datetime('now')")
        d.execute(f"update {table} set {', '.join(sets)} where id = ?", (*args, rid))


def _sse(gen):
    async def body():
        async for kind, data in gen:
            yield f"event: {kind}\ndata: {json.dumps(data)}\n\n"
    return StreamingResponse(body(), media_type="text/event-stream",
                             headers={"cache-control": "no-cache", "x-accel-buffering": "no"})


# --- Characters -------------------------------------------------------------------------------

CHAR_FIELDS = ("name", "personality", "inner_life", "key_memories", "voice", "directive", "model", "hue",
               "pronouns", "appearance", "person", "style", "persona_id", "sore_spot")


@app.get("/api/characters")
def characters():
    with db.connect() as d:
        out = db.rows(d.execute("select id, name, avatar, hue, pronouns, model, substr(personality, 1, 160) as personality "
                                "from character order by name collate nocase"))
        ties: dict[int, list] = {}
        for r in d.execute("select m.character_id, s.id, s.title from cast_member m join story s on s.id = m.story_id "
                           "order by s.updated_at desc"):
            ties.setdefault(r["character_id"], []).append({"id": r["id"], "title": r["title"]})
        for c in out:
            c["stories"] = ties.get(c["id"], [])
            c["model_label"] = models.label(c["model"]).split(" · ")[0] if c["model"] else ""
        return out


@app.post("/api/characters")
async def new_character(request: Request):
    body = await _body(request)
    name = str(body.get("name", "")).strip() or "New character"
    with db.connect() as d:
        cid = d.execute("insert into character(name, hue) values (?, ?)", (name, secrets.randbelow(360))).lastrowid
        _update(d, "character", cid, body, CHAR_FIELDS[1:])
        if body.get("story_id"):
            d.execute("insert or ignore into cast_member(story_id, character_id) values (?, ?)", (body["story_id"], cid))
        return {"id": cid}


@app.get("/api/characters/{cid}")
def get_character(cid: int):
    with db.connect() as d:
        ch = _one(d, "select * from character where id = ?", (cid,))
        ch["corrections"] = db.rows(d.execute("select * from correction where character_id = ? order by id", (cid,)))
        ch["examples"] = db.rows(d.execute("select * from example where character_id = ? order by id desc", (cid,)))
        ch["journal"] = db.rows(d.execute("select * from journal where character_id = ? order by id", (cid,)))
        stories = []
        for s in d.execute("select s.id, s.title from cast_member m join story s on s.id = m.story_id "
                           "where m.character_id = ? order by s.updated_at desc", (cid,)):
            mems = db.rows(d.execute(
                "select m.*, sc.title as scene_title from memory m left join scene sc on sc.id = m.scene_id "
                "where m.character_id = ? and m.story_id = ? order by m.pinned desc, coalesce(sc.seq, 0), m.id", (cid, s["id"])))
            learned = d.execute("select text from learned where story_id = ? and character_id = ?", (s["id"], cid)).fetchone()
            arc = db.rows(d.execute("select * from feeling where story_id = ? and character_id = ? order by id desc limit 40",
                                    (s["id"], cid)))
            stories.append({"id": s["id"], "title": s["title"], "memories": mems,
                            "learned": learned["text"] if learned else "", "feelings": arc})
        ch["stories"] = stories
        ch["model_label"] = models.label(ch["model"])
        ch["names"] = engine.names(d)
        return ch


@app.patch("/api/characters/{cid}")
async def edit_character(cid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        _one(d, "select id from character where id = ?", (cid,))
        _update(d, "character", cid, body, CHAR_FIELDS)
    return {"ok": True}


@app.delete("/api/characters/{cid}")
def delete_character(cid: int):
    with db.connect() as d:
        d.execute("delete from character where id = ?", (cid,))
    return {"ok": True}


@app.post("/api/characters/{cid}/avatar")
async def avatar(cid: int, file: UploadFile):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "image")
    data = await file.read()
    if len(data) > 8_000_000:
        raise HTTPException(413, "big")
    name = images.save(data, cid)
    with db.connect() as d:
        d.execute("update character set avatar = ? where id = ?", (name, cid))
        d.execute("insert into portrait(character_id, file, style) values (?, ?, 'upload')", (cid, name))
    return {"avatar": name}


# --- Portraits ----------------------------------------------------------------------------------

@app.get("/api/portraits")
def portraits():
    with db.connect() as d:
        return db.rows(d.execute("select p.*, c.name from portrait p left join character c on c.id = p.character_id "
                                 "order by p.id desc"))


@app.post("/api/characters/{cid}/portraits")
async def new_portrait(cid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        ch = _one(d, "select * from character where id = ?", (cid,))
        ref = db.setting(d, "portrait_model")
    style = body.get("style") or "painted"
    prompt = images.prompt_for(ch, style, body.get("description"))
    try:
        data = await images.generate(ref, prompt)
    except models.ModelError as e:
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=502)
    name = images.save(data, cid)
    with db.connect() as d:
        pid = d.execute("insert into portrait(character_id, file, prompt, style) values (?, ?, ?, ?)",
                        (cid, name, prompt, style)).lastrowid
        d.execute("update character set avatar = ? where id = ?", (name, cid))
        return db.row(d.execute("select * from portrait where id = ?", (pid,)).fetchone())


@app.post("/api/characters/{cid}/portrait")
async def use_portrait(cid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        p = _one(d, "select * from portrait where id = ?", (int(body["portrait_id"]),))
        d.execute("update character set avatar = ? where id = ?", (p["file"], cid))
    return {"avatar": p["file"]}


@app.delete("/api/portraits/{pid}")
def delete_portrait(pid: int):
    with db.connect() as d:
        p = _one(d, "select * from portrait where id = ?", (pid,))
        d.execute("delete from portrait where id = ?", (pid,))
        used = d.execute("select 1 from character where avatar = ?", (p["file"],)).fetchone()
    if not used:
        f = config.path("avatars", Path(p["file"]).name)
        if f.exists():
            f.unlink()
    return {"ok": True}


@app.get("/avatars/{name}")
def avatar_file(name: str):
    p = config.path("avatars", Path(name).name)
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, headers={"cache-control": "max-age=31536000, immutable"})


@app.post("/api/characters/{cid}/draft")
async def draft(cid: int, request: Request):
    body = await _body(request)
    words = str(body.get("words", "")).strip()
    try:
        return await engine.draft_character(cid, words, replace=bool(body.get("replace")))
    except models.ModelError as e:
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=502)


@app.post("/api/characters/{cid}/corrections")
async def add_correction(cid: int, request: Request):
    body = await _body(request)
    text = str(body.get("text", "")).strip()
    if not text:
        raise HTTPException(400, "empty")
    with db.connect() as d:
        return {"id": d.execute("insert into correction(character_id, text) values (?, ?)", (cid, text)).lastrowid}


@app.patch("/api/corrections/{rid}")
async def edit_correction(rid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        _update(d, "correction", rid, body, ("text",))
    return {"ok": True}


@app.delete("/api/corrections/{rid}")
def delete_correction(rid: int):
    with db.connect() as d:
        d.execute("delete from correction where id = ?", (rid,))
    return {"ok": True}


@app.delete("/api/examples/{rid}")
def delete_example(rid: int):
    with db.connect() as d:
        ev = d.execute("select event_id from example where id = ?", (rid,)).fetchone()
        d.execute("delete from example where id = ?", (rid,))
        if ev and ev["event_id"]:
            d.execute("update event set rating = 0 where id = ?", (ev["event_id"],))
    return {"ok": True}


# --- Memories, notes, feelings, journal -------------------------------------------------------

@app.post("/api/memories")
async def add_memory(request: Request):
    body = await _body(request)
    with db.connect() as d:
        mid = d.execute("insert into memory(character_id, story_id, text, pinned) values (?, ?, ?, ?)",
                        (body["character_id"], body["story_id"], str(body.get("text", "")).strip(),
                         1 if body.get("pinned") else 0)).lastrowid
    return {"id": mid}


@app.patch("/api/memories/{mid}")
async def edit_memory(mid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        _update(d, "memory", mid, body, ("text", "pinned"))
    return {"ok": True}


@app.delete("/api/memories/{mid}")
def delete_memory(mid: int):
    with db.connect() as d:
        d.execute("update memory set replaced_by = null where replaced_by = ?", (mid,))
        d.execute("delete from memory where id = ?", (mid,))
    return {"ok": True}


@app.put("/api/learned/{sid}/{cid}")
async def set_learned(sid: int, cid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        d.execute("insert into learned(story_id, character_id, text) values (?, ?, ?) on conflict(story_id, character_id) "
                  "do update set text = excluded.text, updated_at = datetime('now')", (sid, cid, str(body.get("text", ""))))
    return {"ok": True}


@app.post("/api/feelings")
async def set_feeling(request: Request):
    """She can set how someone feels by hand; it becomes the latest."""
    body = await _body(request)
    with db.connect() as d:
        fid = d.execute("insert into feeling(story_id, character_id, mood, toward, word, strength, shows) values (?, ?, ?, ?, ?, ?, ?)",
                        (body["story_id"], body["character_id"], str(body.get("mood", "")),
                         json.dumps(body.get("toward") or {}), str(body.get("word", "")),
                         json.dumps(body.get("strength") or {}), json.dumps(body.get("shows") or {}))).lastrowid
    return {"id": fid}


@app.post("/api/journal")
async def add_journal(request: Request):
    body = await _body(request)
    text = str(body.get("text", "")).strip()
    if not text:
        raise HTTPException(400, "empty")
    with db.connect() as d:
        jid = d.execute("insert into journal(story_id, character_id, title, keys, text) values (?, ?, ?, ?, ?)",
                        (body.get("story_id"), body.get("character_id"), str(body.get("title", "")),
                         str(body.get("keys", "")), text)).lastrowid
    return {"id": jid}


@app.patch("/api/journal/{jid}")
async def edit_journal(jid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        _update(d, "journal", jid, body, ("title", "keys", "text", "enabled", "pinned"))
    return {"ok": True}


@app.post("/api/journal/try")
async def journal_try(request: Request):
    """Which entries a line would bring to mind, in the journal she's looking at (plus the shared one)."""
    body = await _body(request)
    sid, cid = body.get("story_id"), body.get("character_id")
    with db.connect() as d:
        if sid:
            rows = d.execute("select * from journal where (story_id = ? or story_id is null) and character_id is null order by id", (sid,))
        elif cid:
            rows = d.execute("select * from journal where story_id is null and (character_id = ? or character_id is null) order by id", (cid,))
        else:
            rows = d.execute("select * from journal where story_id is null and character_id is null order by id")
        hits, over = engine.journal_pick(db.rows(rows), str(body.get("text", "")))
    name = lambda j: {"id": j["id"], "title": j["title"] or j["text"][:40]}
    return {"hits": [name(j) for j in hits], "over": [name(j) for j in over]}


@app.delete("/api/journal/{jid}")
def delete_journal(jid: int):
    with db.connect() as d:
        d.execute("delete from journal where id = ?", (jid,))
    return {"ok": True}


@app.get("/api/journal")
def global_journal():
    with db.connect() as d:
        return db.rows(d.execute("select * from journal where story_id is null and character_id is null order by id"))


# --- Stories ----------------------------------------------------------------------------------

STORY_FIELDS = ("title", "premise", "directive", "style", "length", "memory", "turns", "model", "person", "personas")


@app.get("/api/stories")
def stories():
    with db.connect() as d:
        out = db.rows(d.execute("select id, title, substr(premise, 1, 200) as premise, updated_at from story order by updated_at desc"))
        for s in out:
            s["cast"] = db.rows(d.execute("select c.id, c.name, c.avatar, c.hue from cast_member m join character c "
                                          "on c.id = m.character_id where m.story_id = ? order by c.name", (s["id"],)))
            s["scenes"] = d.execute("select count(*) from scene where story_id = ?", (s["id"],)).fetchone()[0]
        return out


@app.post("/api/stories")
async def new_story(request: Request):
    body = await _body(request)
    with db.connect() as d:
        sid = d.execute("insert into story(title) values (?)", (str(body.get("title", "")).strip() or "New story",)).lastrowid
        _update(d, "story", sid, body, STORY_FIELDS[1:])
    return {"id": sid}


@app.get("/api/stories/{sid}")
def get_story(sid: int):
    with db.connect() as d:
        s = _one(d, "select * from story where id = ?", (sid,))
        s["cast"] = engine.cast(d, sid)
        s["scenes"] = db.rows(d.execute("select * from scene where story_id = ? order by seq desc, id desc", (sid,)))
        for sc in s["scenes"]:
            sc["here"] = [c["id"] for c in engine.present(d, sc["id"])]
            seen = set()
            for e in d.execute("select witnesses from event where scene_id = ?", (sc["id"],)):
                seen.update(json.loads(e["witnesses"] or "[]"))
            sc["everyone"] = sorted(seen | set(sc["here"]))
            sc["lines"] = d.execute("select count(*) from event where scene_id = ? and kind in ('you','character')",
                                    (sc["id"],)).fetchone()[0]
        s["journal"] = db.rows(d.execute("select * from journal where story_id = ? order by id", (sid,)))
        s["feelings"] = {}
        for c in s["cast"]:
            f = engine.feeling_now(d, sid, c["id"])
            if f:
                s["feelings"][str(c["id"])] = f
        s["learned"] = {str(r["character_id"]): r["text"] for r in d.execute(
            "select character_id, text from learned where story_id = ?", (sid,))}
        s["model_label"] = models.label(s["model"])
        s["names"] = engine.names(d)
        return s


@app.patch("/api/stories/{sid}")
async def edit_story(sid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        _one(d, "select id from story where id = ?", (sid,))
        _update(d, "story", sid, body, STORY_FIELDS)
    return {"ok": True}


@app.delete("/api/stories/{sid}")
def delete_story(sid: int):
    with db.connect() as d:
        bgs = [r["background"] for r in d.execute("select background from scene where story_id = ? and background != ''", (sid,))]
        d.execute("delete from story where id = ?", (sid,))
    for bg in bgs:
        _drop_background(bg)
    return {"ok": True}


@app.post("/api/stories/{sid}/cast")
async def add_cast(sid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        d.execute("insert or ignore into cast_member(story_id, character_id) values (?, ?)", (sid, int(body["character_id"])))
    return {"ok": True}


@app.delete("/api/stories/{sid}/cast/{cid}")
def remove_cast(sid: int, cid: int):
    with db.connect() as d:
        d.execute("delete from cast_member where story_id = ? and character_id = ?", (sid, cid))
    return {"ok": True}


@app.get("/api/stories/{sid}/export")
def export_story(sid: int):
    with db.connect() as d:
        s = _one(d, "select * from story where id = ?", (sid,))
        who = engine.names(d)
        out = [f"# {s['title']}", ""]
        if s["premise"]:
            out += [s["premise"], ""]
        for sc in d.execute("select * from scene where story_id = ? order by seq, id", (sid,)):
            out += [f"## {sc['title'] or 'Untitled'}", ""]
            if sc["setting"]:
                out += [f"*{sc['setting']}*", ""]
            for e in db.rows(d.execute("select * from event where scene_id = ? order by seq", (sc["id"],))):
                text = engine.line(e, who)
                if e["kind"] in ("enter", "leave"):
                    out += [f"*{text.strip('[]')}*", ""]
                    continue
                name, _, rest = text.partition(": ") if not text.startswith("[Narrator]") else ("Narrator", "", text[11:])
                star = " ⭐" if e["starred"] else ""
                out += [f"**{name}:**{star} {rest}", ""]
                if e["idea"]:
                    out += [f"> {e['idea']}", ""]
        md = "\n".join(out)
    fname = "".join(ch for ch in s["title"] if ch.isalnum() or ch in " -_").strip() or "story"
    return PlainTextResponse(md, media_type="text/markdown; charset=utf-8",
                             headers={"content-disposition": f'attachment; filename="{fname}.md"'})


# --- Scenes -----------------------------------------------------------------------------------

def _enter(d, scene_id: int, cid: int):
    if d.execute("select 1 from presence where scene_id = ? and character_id = ? and left_seq is null",
                 (scene_id, cid)).fetchone():
        return
    seq = engine.next_seq(d, scene_id)
    here = [c["id"] for c in engine.present(d, scene_id)] + [cid]
    d.execute("insert into presence(scene_id, character_id, joined_seq) values (?, ?, ?)", (scene_id, cid, seq))
    d.execute("insert into event(scene_id, seq, kind, character_id, witnesses) values (?, ?, 'enter', ?, ?)",
              (scene_id, seq, cid, json.dumps(here)))


def _leave(d, scene_id: int, cid: int) -> bool:
    if not d.execute("select 1 from presence where scene_id = ? and character_id = ? and left_seq is null",
                     (scene_id, cid)).fetchone():
        return False
    seq = engine.next_seq(d, scene_id)
    here = [c["id"] for c in engine.present(d, scene_id)]
    d.execute("insert into event(scene_id, seq, kind, character_id, witnesses) values (?, ?, 'leave', ?, ?)",
              (scene_id, seq, cid, json.dumps(here)))
    d.execute("update presence set left_seq = ? where scene_id = ? and character_id = ? and left_seq is null",
              (seq, scene_id, cid))
    return True


@app.post("/api/stories/{sid}/scenes")
async def new_scene(sid: int, request: Request):
    """A new scene. from_scene: the characters picked walk out of that scene into this one."""
    body = await _body(request)
    leavers = []
    with db.connect() as d:
        _one(d, "select id from story where id = ?", (sid,))
        seq = (d.execute("select max(seq) from scene where story_id = ?", (sid,)).fetchone()[0] or 0) + 1
        scid = d.execute("insert into scene(story_id, title, setting, aim, seq, whatif) values (?, ?, ?, ?, ?, ?)",
                         (sid, str(body.get("title", "")), str(body.get("setting", "")), str(body.get("aim", "")), seq,
                          1 if body.get("whatif") else 0)).lastrowid
        for cid in body.get("characters") or []:
            d.execute("insert or ignore into cast_member(story_id, character_id) values (?, ?)", (sid, int(cid)))
            if body.get("from_scene") and _leave(d, int(body["from_scene"]), int(cid)):
                leavers.append((int(body["from_scene"]), int(cid)))
            _enter(d, scid, int(cid))
        d.execute("update story set updated_at = datetime('now') where id = ?", (sid,))
    for old, cid in leavers:
        await engine.condense(old, cid)
    return {"id": scid}


@app.get("/api/scenes/{scid}")
def get_scene(scid: int):
    with db.connect() as d:
        sc = _one(d, "select * from scene where id = ?", (scid,))
        story = _one(d, "select * from story where id = ?", (sc["story_id"],))
        sc["story"] = {k: story[k] for k in ("id", "title", "personas", "turns", "memory", "model", "person")}
        sc["story"]["model_label"] = models.label(story["model"])
        sc["personas"] = db.rows(d.execute("select * from persona order by name collate nocase"))
        sc["cast"] = engine.cast(d, story["id"])
        sc["here"] = [c["id"] for c in engine.present(d, scid)]
        sc["events"] = [engine.event_out(d, r["id"]) for r in d.execute("select id from event where scene_id = ? order by seq", (scid,))]
        sc["feelings"] = {}
        for c in sc["cast"]:
            f = engine.feeling_now(d, story["id"], c["id"])
            if f:
                sc["feelings"][str(c["id"])] = f
        sc["names"] = engine.names(d)
        sc["others"] = db.rows(d.execute("select id, title from scene where story_id = ? and id != ? order by seq desc",
                                         (story["id"], scid)))
        return sc


@app.patch("/api/scenes/{scid}")
async def edit_scene(scid: int, request: Request):
    body = await _body(request)
    if "whatif" in body:
        body["whatif"] = 1 if body["whatif"] else 0
    with db.connect() as d:
        _update(d, "scene", scid, body, ("title", "setting", "aim", "whatif"))
    return {"ok": True}


@app.delete("/api/scenes/{scid}")
def delete_scene(scid: int):
    with db.connect() as d:
        bg = (d.execute("select background from scene where id = ?", (scid,)).fetchone() or {"background": ""})["background"]
        d.execute("delete from memory where scene_id = ?", (scid,))
        d.execute("delete from scene where id = ?", (scid,))
    _drop_background(bg)
    return {"ok": True}


# A picture behind a scene's lines, chosen by her (the page dims it in the theme's colour).
@app.post("/api/scenes/{scid}/background")
async def scene_background(scid: int, file: UploadFile):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "image")
    data = await file.read()
    if len(data) > 12_000_000:
        raise HTTPException(413, "big")
    with db.connect() as d:
        old = _one(d, "select background from scene where id = ?", (scid,))["background"]
        name = images.save(data, f"scene{scid}", "backgrounds")
        d.execute("update scene set background = ? where id = ?", (name, scid))
    _drop_background(old)
    return {"background": name}


@app.delete("/api/scenes/{scid}/background")
def scene_background_off(scid: int):
    with db.connect() as d:
        old = _one(d, "select background from scene where id = ?", (scid,))["background"]
        d.execute("update scene set background = '' where id = ?", (scid,))
    _drop_background(old)
    return {"ok": True}


def _drop_background(name: str | None):
    if name:
        f = config.path("backgrounds", Path(name).name)
        if f.exists():
            f.unlink()


@app.get("/backgrounds/{name}")
def background_file(name: str):
    p = config.path("backgrounds", Path(name).name)
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, headers={"cache-control": "max-age=31536000, immutable"})


@app.post("/api/scenes/{scid}/presence")
async def presence(scid: int, request: Request):
    body = await _body(request)
    cid = int(body["character_id"])
    left = False
    with db.connect() as d:
        sc = _one(d, "select * from scene where id = ?", (scid,))
        d.execute("insert or ignore into cast_member(story_id, character_id) values (?, ?)", (sc["story_id"], cid))
        if body.get("here"):
            _enter(d, scid, cid)
        else:
            left = _leave(d, scid, cid)
    if left:
        await engine.condense(scid, cid)
    return {"ok": True}


@app.post("/api/scenes/{scid}/end")
async def end_scene(scid: int):
    await engine.end_scene(scid)
    return {"ok": True}


@app.post("/api/scenes/{scid}/reopen")
def reopen_scene(scid: int):
    with db.connect() as d:
        d.execute("update scene set state = 'open', ended_at = null where id = ?", (scid,))
    return {"ok": True}


@app.post("/api/scenes/{scid}/say")
async def say(scid: int, request: Request):
    body = await _body(request)
    text = str(body.get("text", "")).strip()
    if not text:
        raise HTTPException(400, "empty")
    with db.connect() as d:
        sc = _one(d, "select * from scene where id = ?", (scid,))
        seq = engine.next_seq(d, scid)
        here = [c["id"] for c in engine.present(d, scid)]
        speaker = str(body.get("as", ""))
        eid = d.execute("insert into event(scene_id, seq, kind, speaker, content, witnesses) values (?, ?, 'you', ?, ?, ?)",
                        (scid, seq, speaker, text, json.dumps(here))).lastrowid
        d.execute("update story set updated_at = datetime('now') where id = ?", (sc["story_id"],))
        # Speaking as one of her personas puts that persona in the story.
        p = d.execute("select id from persona where name = ?", (speaker,)).fetchone() if speaker else None
        if p:
            story = db.row(d.execute("select personas from story where id = ?", (sc["story_id"],)).fetchone())
            if p["id"] not in story["personas"]:
                d.execute("update story set personas = ? where id = ?",
                          (json.dumps(story["personas"] + [p["id"]]), sc["story_id"]))
        return engine.event_out(d, eid)


@app.post("/api/scenes/{scid}/suggest")
async def suggest(scid: int, request: Request):
    body = await _body(request)
    try:
        return {"text": await engine.suggest_line(scid, str(body.get("as", "")))}
    except models.ModelError as e:
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=502)


@app.post("/api/import")
async def bring_in(file: UploadFile, target: str = Form(...), target_id: int = Form(0)):
    """A file she brings in: into a scene (everyone there reads it), onto a character, or into a story's journal."""
    data = await file.read()
    if len(data) > 20_000_000:
        raise HTTPException(413, "big")
    name = Path(file.filename or "Untitled").name
    try:
        text = docs.extract(name, data)
    except docs.Unreadable:
        raise HTTPException(415, "unreadable")
    with db.connect() as d:
        if target == "scene":
            _one(d, "select id from scene where id = ?", (target_id,))
            seq = engine.next_seq(d, target_id)
            here = [c["id"] for c in engine.present(d, target_id)]
            eid = d.execute("insert into event(scene_id, seq, kind, speaker, content, witnesses) values (?, ?, 'doc', ?, ?, ?)",
                            (target_id, seq, name, text, json.dumps(here))).lastrowid
            return {"event": engine.event_out(d, eid), "words": docs.words(text)}
        if target in ("character", "story"):
            col = "character_id" if target == "character" else "story_id"
            jid = d.execute(f"insert into journal({col}, title, keys, text) values (?, ?, '', ?)",
                            (target_id, name, text)).lastrowid
            return {"journal": jid, "words": docs.words(text)}
        if target == "shared":
            jid = d.execute("insert into journal(title, keys, text) values (?, '', ?)", (name, text)).lastrowid
            return {"journal": jid, "words": docs.words(text)}
    raise HTTPException(400, "target")


@app.post("/api/journal/split")
async def journal_split(file: UploadFile, story_id: int = Form(0)):
    """Her pages, split into journal entries for her to look over. Nothing is saved yet."""
    data = await file.read()
    if len(data) > 20_000_000:
        raise HTTPException(413, "big")
    try:
        text = docs.extract(Path(file.filename or "Untitled").name, data)
    except docs.Unreadable:
        raise HTTPException(415, "unreadable")
    try:
        return await engine.split_into_entries(text, story_id or None)
    except models.ModelError as e:
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=502)


@app.post("/api/journal/batch")
async def journal_batch(request: Request):
    body = await _body(request)
    with db.connect() as d:
        n = 0
        for e in body.get("entries") or []:
            if str(e.get("text") or "").strip():
                d.execute("insert into journal(story_id, character_id, title, keys, text) values (?, ?, ?, ?, ?)",
                          (body.get("story_id"), body.get("character_id"), str(e.get("title") or ""), str(e.get("keys") or ""),
                           str(e["text"]).strip()))
                n += 1
    return {"added": n}


@app.post("/api/scenes/{scid}/journal-entry")
async def scene_journal_entry(scid: int, request: Request):
    body = await _body(request)
    try:
        return await engine.entry_from_lines(scid, [int(i) for i in body.get("event_ids") or []])
    except models.ModelError as e:
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=502)


# --- Personas: the people she plays ---------------------------------------------------------------

@app.get("/api/personas")
def personas():
    with db.connect() as d:
        return db.rows(d.execute("select * from persona order by name collate nocase"))


@app.post("/api/personas")
async def new_persona(request: Request):
    body = await _body(request)
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(400, "name")
    with db.connect() as d:
        pid = d.execute("insert into persona(name, pronouns, about) values (?, ?, ?)",
                        (name, str(body.get("pronouns", "")), str(body.get("about", "")))).lastrowid
    return {"id": pid}


@app.patch("/api/personas/{pid}")
async def edit_persona(pid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        _update(d, "persona", pid, body, ("name", "pronouns", "about"))
    return {"ok": True}


@app.delete("/api/personas/{pid}")
def delete_persona(pid: int):
    with db.connect() as d:
        d.execute("delete from persona where id = ?", (pid,))
        d.execute("update character set persona_id = null where persona_id = ?", (pid,))
        for s in db.rows(d.execute("select id, personas from story")):
            if pid in s["personas"]:
                d.execute("update story set personas = ? where id = ?",
                          (json.dumps([x for x in s["personas"] if x != pid]), s["id"]))
    return {"ok": True}


@app.post("/api/scenes/{scid}/next")
async def who_next(scid: int, request: Request):
    body = await _body(request)
    return {"speakers": await engine.pick(scid, more=bool(body.get("more")))}


@app.post("/api/scenes/{scid}/turn")
async def take_turn(scid: int, request: Request):
    body = await _body(request)
    return _sse(engine.turn(scid, int(body["character_id"]), model=body.get("model") or None))


# --- One line of a scene ----------------------------------------------------------------------

@app.post("/api/events/{eid}/redo")
async def redo(eid: int, request: Request):
    body = await _body(request)
    return _sse(engine.turn(0, 0, redo=eid, model=body.get("model") or None,
                            note=(body.get("note") or "").strip() or None, save_note=bool(body.get("save"))))


@app.post("/api/events/{eid}/continue")
async def go_on(eid: int):
    return _sse(engine.turn(0, 0, cont=eid))


@app.post("/api/events/{eid}/pick")
async def pick_version(eid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        e = _one(d, "select * from event where id = ?", (eid,))
        i = int(body.get("index", 0))
        v = e["versions"] or []
        if not 0 <= i < len(v):
            raise HTTPException(400, "index")
        d.execute("update event set pick = ?, content = ?, inner = ?, model = ?, rating = 0 where id = ?",
                  (i, v[i]["content"], v[i].get("inner", ""), v[i].get("model", ""), eid))
        d.execute("delete from example where event_id = ?", (eid,))
        return engine.event_out(d, eid)


@app.post("/api/events/{eid}/rate")
async def rate(eid: int, request: Request):
    body = await _body(request)
    value = int(body.get("value", 0))
    with db.connect() as d:
        e = _one(d, "select * from event where id = ?", (eid,))
        d.execute("update event set rating = ? where id = ?", (value, eid))
        d.execute("delete from example where event_id = ?", (eid,))
        if value > 0 and e["kind"] == "character":
            d.execute("insert into example(character_id, text, event_id) values (?, ?, ?)",
                      (e["character_id"], e["content"][:1200], eid))
        return engine.event_out(d, eid)


@app.post("/api/events/{eid}/star")
async def star(eid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        _update(d, "event", eid, {"starred": 1 if body.get("starred") else 0, **({"idea": body["idea"]} if "idea" in body else {})},
                ("starred", "idea"))
        return engine.event_out(d, eid)


@app.patch("/api/events/{eid}")
async def edit_event(eid: int, request: Request):
    body = await _body(request)
    with db.connect() as d:
        e = _one(d, "select * from event where id = ?", (eid,))
        if "content" in body:
            v = e["versions"] or []
            if v and 0 <= e["pick"] < len(v):
                v[e["pick"]]["content"] = body["content"]
            d.execute("update event set content = ?, versions = ? where id = ?", (body["content"], json.dumps(v), eid))
        if "inner" in body:
            d.execute("update event set inner = ? where id = ?", (body["inner"], eid))
        if "speaker" in body:
            d.execute("update event set speaker = ? where id = ?", (body["speaker"], eid))
        return engine.event_out(d, eid)


@app.delete("/api/events/{eid}")
def delete_event(eid: int):
    with db.connect() as d:
        e = d.execute("select scene_id, seq from event where id = ?", (eid,)).fetchone()
        if e:
            engine.forget_lines(d, e["scene_id"], e["seq"], e["seq"])
        d.execute("delete from example where event_id = ?", (eid,))
        d.execute("delete from feeling where event_id = ?", (eid,))
        d.execute("delete from event where id = ?", (eid,))
    return {"ok": True}


@app.post("/api/events/{eid}/rewind")
def rewind(eid: int):
    """Take back this line and everything after it."""
    with db.connect() as d:
        e = _one(d, "select * from event where id = ?", (eid,))
        gone = [r["id"] for r in d.execute("select id from event where scene_id = ? and seq >= ?", (e["scene_id"], e["seq"]))]
        for g in gone:
            d.execute("delete from example where event_id = ?", (g,))
            d.execute("delete from feeling where event_id = ?", (g,))
        d.execute("delete from event where scene_id = ? and seq >= ?", (e["scene_id"], e["seq"]))
        engine.forget_lines(d, e["scene_id"], e["seq"])
        # Presence that started in what was taken back is undone; leaving that was taken back is undone.
        d.execute("delete from presence where scene_id = ? and joined_seq >= ?", (e["scene_id"], e["seq"]))
        d.execute("update presence set left_seq = null where scene_id = ? and left_seq >= ?", (e["scene_id"], e["seq"]))
        d.execute("update condensed set upto = min(upto, ?) where scene_id = ?", (e["seq"] - 1, e["scene_id"]))
    return {"ok": True}


@app.get("/api/ideas")
def ideas():
    with db.connect() as d:
        rs = db.rows(d.execute(
            "select e.id, e.content, e.idea, e.kind, e.speaker, e.character_id, e.scene_id, e.created_at, "
            "sc.title as scene_title, s.title as story_title, s.id as story_id, c.name, c.avatar, c.hue "
            "from event e join scene sc on sc.id = e.scene_id join story s on s.id = sc.story_id "
            "left join character c on c.id = e.character_id where e.starred = 1 order by e.id desc"))
        return rs


# --- Settings and models ----------------------------------------------------------------------

SETTINGS = ("default_model", "helper_model", "portrait_model", "thinking", "short_term", "recall", "feelings", "round", "repetition")


@app.get("/api/settings")
def get_settings():
    with db.connect() as d:
        conns = db.rows(d.execute("select * from connection order by id"))
        for c in conns:
            key = c.pop("api_key", "") or ""
            c["has_key"] = bool(key)
            c["key_tail"] = key[-4:] if len(key) > 8 else ""
        vals = {k: db.setting(d, k) for k in SETTINGS}
        labels = {k: models.label(vals[k]) for k in ("default_model", "helper_model", "portrait_model")}
    return {"connections": conns, "settings": vals, "labels": labels, "chatgpt": chatgpt.status(),
            "presets": {k: {**p, "draws": k not in models.DRAWS_NOT and k not in models.TURNS} for k, p in models.PRESETS.items()},
            "port": config.PORT, "name": config.NAME, "signin": bool(config.PASSWORD or people.load())}


@app.put("/api/settings")
async def put_settings(request: Request):
    body = await _body(request)
    with db.connect() as d:
        for k in SETTINGS:
            if k in body:
                db.set_setting(d, k, body[k] if body[k] not in ("", None) else None)
    return {"ok": True}


@app.post("/api/connections")
async def add_connection(request: Request):
    body = await _body(request)
    preset = body.get("preset", "custom")
    if preset not in models.PRESETS or preset == "chatgpt":
        raise HTTPException(400, "preset")
    p = models.PRESETS[preset]
    with db.connect() as d:
        cid = d.execute("insert into connection(preset, name, base_url, api_key) values (?, ?, ?, ?)",
                        (preset, str(body.get("name") or p["name"]), str(body.get("base_url") or p["base_url"]),
                         str(body.get("api_key", "")).strip())).lastrowid
        if not db.setting(d, "default_model") and body.get("model"):
            db.set_setting(d, "default_model", f"{cid}/{body['model']}")
    return {"id": cid}


@app.patch("/api/connections/{cid}")
async def edit_connection(cid: int, request: Request):
    body = await _body(request)
    if "api_key" in body:
        body["api_key"] = str(body["api_key"]).strip()
    with db.connect() as d:
        _update(d, "connection", cid, body, ("name", "base_url", "api_key"))
    models.forget(cid)
    return {"ok": True}


@app.delete("/api/connections/{cid}")
def delete_connection(cid: int):
    with db.connect() as d:
        c = _one(d, "select * from connection where id = ?", (cid,))
        if c["preset"] == "chatgpt":
            raise HTTPException(400, "chatgpt")
        d.execute("delete from connection where id = ?", (cid,))
    models.forget(cid)
    return {"ok": True}


@app.get("/api/connections/{cid}/models")
async def connection_models(cid: int, fresh: int = 0, kind: str = "text"):
    try:
        return await models.available(cid, fresh=bool(fresh), kind="image" if kind == "image" else "text")
    except models.ModelError as e:
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=502)


@app.post("/api/connections/{cid}/test")
async def test_connection(cid: int, request: Request):
    body = await _body(request)
    ref = f"{cid}/{body.get('model', '')}"
    try:
        reply = await models.complete(ref, "Reply with the single word: ready", [{"role": "user", "content": "Are you there?"}])
        return {"ok": True, "reply": reply.strip()[:200]}
    except models.ModelError as e:
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=502)


@app.post("/api/chatgpt/start")
def chatgpt_start():
    return {"url": chatgpt.start(), "redirect": chatgpt.redirect_uri()}


@app.post("/api/chatgpt/finish")
async def chatgpt_finish(request: Request):
    body = await _body(request)
    try:
        return await chatgpt.finish(chatgpt.parse_callback(str(body.get("url", ""))))
    except chatgpt.SignInError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/auth/callback")
async def chatgpt_callback(request: Request):
    try:
        await chatgpt.finish(dict(request.query_params))
        return RedirectResponse("/#/settings")
    except chatgpt.SignInError as e:
        return RedirectResponse(f"/#/settings?chatgpt={e}")


@app.post("/api/chatgpt/disconnect")
async def chatgpt_disconnect():
    return {"told": await chatgpt.disconnect()}


@app.get("/api/backup")
def backup():
    with db.connect() as d:
        out = {}
        for t in ("character", "correction", "example", "story", "cast_member", "scene", "presence", "event", "memory",
                  "condensed", "learned", "feeling", "journal"):
            out[t] = db.rows(d.execute(f"select * from {t}"))
    return JSONResponse(out, headers={"content-disposition": f'attachment; filename="{config.NAME.lower()}-backup.json"'})


# --- The page ---------------------------------------------------------------------------------

@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse({"name": config.NAME, "short_name": config.NAME, "start_url": "/", "display": "standalone",
                         "background_color": "#120e0f", "theme_color": "#120e0f",
                         "icons": [{"src": "/static/icon.svg", "sizes": "any", "type": "image/svg+xml"},
                                   {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
                                   {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]})


@app.get("/static/{name}")
def static(name: str):
    p = STATIC / Path(name).name
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, headers={"cache-control": "no-cache"})


@app.get("/fonts/{name}")
def fonts(name: str):
    p = STATIC / "fonts" / Path(name).name
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, headers={"cache-control": "max-age=31536000, immutable"})


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html", headers={"cache-control": "no-cache"})
