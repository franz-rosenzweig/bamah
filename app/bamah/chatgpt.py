"""Using a ChatGPT plan, through OpenAI's "Sign in with ChatGPT" for open-source apps.

The sign-in is OpenID Connect with PKCE. OpenAI only sends people back to a loopback address
(http://127.0.0.1:<port>/auth/callback), which is the computer the browser is on:

- on your own computer, that is Bamah itself, and the sign-in finishes by itself;
- on a server, the browser lands on a page that doesn't load, and you paste its address into
  Bamah, which finishes the same sign-in from there.

The tokens are kept in data/chatgpt.json (readable only by Bamah), refreshed before they run out,
and the refresh token is replaced every time OpenAI hands out a new one.
Docs: https://developers.openai.com/siwc/token-sharing-open-source
"""

import asyncio
import base64
import hashlib
import json
import os
import secrets
import time
import uuid
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from . import config, db

ISSUER = "https://auth.openai.com"
AUTHORIZE = ISSUER + "/api/accounts/authorize"
TOKEN = ISSUER + "/api/accounts/oauth/token"
RESOURCE = "https://api.openai.com/v1"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
PLAN_SCOPE = "chatgpt.tokens.use.direct"
DYNAMIC = "dynamic_agent_client"

_lock = asyncio.Lock()
_transport = None


class SignInError(Exception):
    pass


def _http() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=30, transport=_transport)


def redirect_uri() -> str:
    return f"http://127.0.0.1:{config.PORT}/auth/callback"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _creds_file():
    return config.path("chatgpt.json")


def load() -> dict | None:
    f = _creds_file()
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except ValueError:
        return None


def _save(creds: dict):
    f = _creds_file()
    tmp = f.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as out:
        json.dump(creds, out)
    os.replace(tmp, f)


def host_id() -> str:
    """A stable id for this copy of Bamah (OpenAI's ext_agent_host_id)."""
    with db.connect() as d:
        hid = db.setting(d, "chatgpt_host_id")
        if not hid:
            hid = str(uuid.uuid4())
            db.set_setting(d, "chatgpt_host_id", hid)
    return hid


def start() -> str:
    """The address to open for "Continue with ChatGPT"."""
    with db.connect() as d:
        client_id = db.setting(d, "chatgpt_client_id") or DYNAMIC
        verifier = _b64(secrets.token_bytes(48))
        pending = {"state": secrets.token_urlsafe(24), "nonce": secrets.token_urlsafe(24), "verifier": verifier,
                   "client_id": client_id, "at": time.time()}
        db.set_setting(d, "chatgpt_pending", json.dumps(pending))
    params = {
        "response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri(),
        "scope": SCOPES, "state": pending["state"], "nonce": pending["nonce"],
        "code_challenge": _b64(hashlib.sha256(verifier.encode()).digest()), "code_challenge_method": "S256",
        "resource": RESOURCE, "ext_agent_host_id": host_id(),
    }
    if client_id == DYNAMIC:
        params["agent_name_hint"] = config.NAME
    creds = load()
    if creds and creds.get("email"):
        params["login_hint"] = creds["email"]
    return AUTHORIZE + "?" + urlencode(params)


def parse_callback(url_or_query: str) -> dict:
    text = url_or_query.strip()
    query = urlparse(text).query if "://" in text else text.lstrip("?")
    return {k: v[0] for k, v in parse_qs(query).items()}


async def finish(params: dict) -> dict:
    """Finish the sign-in from the callback's query (pasted or received). Returns the account."""
    with db.connect() as d:
        raw = db.setting(d, "chatgpt_pending")
    if not raw:
        raise SignInError("start")
    pending = json.loads(raw)
    if params.get("state") != pending["state"]:
        raise SignInError("state")
    if params.get("error"):
        raise SignInError("denied" if params["error"] == "access_denied" else params["error"])
    if time.time() - pending["at"] > 1800:
        raise SignInError("expired")
    code = params.get("code")
    if not code:
        raise SignInError("code")
    issued = params.get("client_id") or pending["client_id"]
    if pending["client_id"] != DYNAMIC and issued != pending["client_id"]:
        raise SignInError("client")
    async with _http() as c:
        r = await c.post(TOKEN, data={"grant_type": "authorization_code", "client_id": issued, "code": code,
                                      "code_verifier": pending["verifier"], "redirect_uri": redirect_uri(),
                                      "resource": RESOURCE})
    if r.status_code >= 400:
        raise SignInError("invalid_grant" if "invalid_grant" in r.text else f"token {r.status_code}")
    tok = r.json()
    if issued == DYNAMIC:
        # The issued id didn't come back on the callback: take it from the token response, or the ID token's audience.
        import jwt
        aud = jwt.decode(tok["id_token"], options={"verify_signature": False}).get("aud")
        issued = tok.get("client_id") or (aud[0] if isinstance(aud, list) else aud) or ""
        if not issued or issued == DYNAMIC:
            raise SignInError("client")
    claims = await _verify(tok["id_token"], issued, pending["nonce"])
    scopes = (tok.get("scope") or "").split()
    if PLAN_SCOPE not in scopes:
        raise SignInError("scope")
    creds = {"client_id": issued, "sub": claims["sub"], "email": claims.get("email", ""),
             "name": claims.get("name", ""), "id_token": tok["id_token"], "access_token": tok["access_token"],
             "refresh_token": tok.get("refresh_token", ""), "token_type": tok.get("token_type", "Bearer"),
             "expires_at": time.time() + int(tok.get("expires_in", 3600)), "scopes": scopes,
             "saved_at": time.time(), "ext_agent_host_id": host_id()}
    _save(creds)
    with db.connect() as d:
        db.set_setting(d, "chatgpt_client_id", issued)
        db.set_setting(d, "chatgpt_pending", None)
        if not d.execute("select 1 from connection where preset = 'chatgpt'").fetchone():
            d.execute("insert into connection(preset, name) values ('chatgpt', 'ChatGPT')")
    return {"email": creds["email"], "name": creds["name"]}


async def _verify(id_token: str, client_id: str, nonce: str) -> dict:
    import jwt

    async with _http() as c:
        oidc = (await c.get(ISSUER + "/.well-known/openid-configuration")).json()
        jwks = (await c.get(oidc["jwks_uri"])).json()
    header = jwt.get_unverified_header(id_token)
    keys = {k.get("kid"): k for k in jwks.get("keys", [])}
    jwk = keys.get(header.get("kid"))
    if not jwk:
        raise SignInError("id_token")
    key = jwt.PyJWK(jwk).key
    try:
        claims = jwt.decode(id_token, key, algorithms=[header.get("alg", "RS256")], audience=client_id,
                            issuer=oidc.get("issuer", ISSUER))
    except jwt.PyJWTError as e:
        raise SignInError("id_token") from e
    if claims.get("nonce") != nonce:
        raise SignInError("nonce")
    return claims


async def access_token(force: bool = False) -> str:
    from .models import ModelError

    async with _lock:
        creds = load()
        if not creds:
            raise ModelError("setup", "ChatGPT isn't connected")
        if force or creds["expires_at"] - time.time() < 120:
            async with _http() as c:
                r = await c.post(TOKEN, data={"grant_type": "refresh_token", "client_id": creds["client_id"],
                                              "refresh_token": creds["refresh_token"], "resource": RESOURCE})
            if r.status_code >= 400:
                raise ModelError("key", "ChatGPT needs signing in again")
            tok = r.json()
            creds["access_token"] = tok["access_token"]
            creds["refresh_token"] = tok.get("refresh_token") or creds["refresh_token"]
            creds["expires_at"] = time.time() + int(tok.get("expires_in", 3600))
            if tok.get("scope"):
                creds["scopes"] = tok["scope"].split()
            creds["saved_at"] = time.time()
            _save(creds)
        return creds["access_token"]


async def disconnect() -> bool:
    """Revoke the refresh token at OpenAI and forget the tokens. False if OpenAI couldn't be told."""
    creds = load()
    told = True
    if creds and creds.get("refresh_token"):
        try:
            async with _http() as c:
                oidc = (await c.get(ISSUER + "/.well-known/openid-configuration")).json()
                r = await c.post(oidc["revocation_endpoint"], data={
                    "token": creds["refresh_token"], "token_type_hint": "refresh_token", "client_id": creds["client_id"]})
                told = r.status_code == 200
        except (httpx.HTTPError, KeyError, ValueError):
            told = False
    f = _creds_file()
    if f.exists():
        f.unlink()
    with db.connect() as d:
        d.execute("delete from connection where preset = 'chatgpt'")
    return told


def status() -> dict | None:
    creds = load()
    if not creds:
        return None
    return {"email": creds.get("email", ""), "name": creds.get("name", "")}
