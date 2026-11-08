import base64
import hashlib
import json
import time
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from bamah import chatgpt, models

from .conftest import stream

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
JWK = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key()))
JWK["kid"] = "k1"


class FakeOpenAI:
    def __init__(self):
        self.seen = []
        self.nonce = None

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.seen.append(req)
        url = str(req.url)
        if url.endswith("/.well-known/openid-configuration"):
            return httpx.Response(200, json={"issuer": "https://auth.openai.com", "jwks_uri": "https://auth.openai.com/jwks",
                                             "revocation_endpoint": "https://auth.openai.com/revoke"})
        if url.endswith("/jwks"):
            return httpx.Response(200, json={"keys": [JWK]})
        if url.endswith("/oauth/token"):
            form = parse_qs(req.content.decode())
            if form["grant_type"] == ["authorization_code"]:
                assert form["client_id"] == ["oaiapp_123"] and form["resource"] == ["https://api.openai.com/v1"]
                assert form["redirect_uri"][0].startswith("http://127.0.0.1:")
                idt = jwt.encode({"iss": "https://auth.openai.com", "aud": "oaiapp_123", "sub": "user-1", "email": "a@b.c",
                                  "nonce": self.nonce, "exp": time.time() + 600}, KEY, algorithm="RS256", headers={"kid": "k1"})
                return httpx.Response(200, json={"id_token": idt, "access_token": "at-1", "refresh_token": "rt-1",
                                                 "expires_in": 3600, "scope": chatgpt.SCOPES})
            assert form["refresh_token"] == ["rt-1"]
            return httpx.Response(200, json={"access_token": "at-2", "refresh_token": "rt-2", "expires_in": 3600})
        if url.endswith("/v1/models"):
            return httpx.Response(200, json={"models": [{"slug": "gpt-x", "display_name": "GPT X", "visibility": "list"},
                                                       {"slug": "hidden", "visibility": "hide"}]})
        if url.endswith("/v1/responses"):
            body = json.loads(req.content)
            assert body["store"] is False and body["stream"] is True and "instructions" in body
            assert all(m["role"] in ("user", "assistant") for m in body["input"])
            events = [{"type": "response.output_text.delta", "delta": "<inner>Calm.</inner>"},
                      {"type": "response.output_text.delta", "delta": "Hi."}, {"type": "response.completed"}]
            sse = "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events)
            return httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})
        if url.endswith("/revoke"):
            return httpx.Response(200)
        return httpx.Response(404)


@pytest.fixture
def openai(app, monkeypatch):
    fake = FakeOpenAI()
    t = httpx.MockTransport(fake)
    monkeypatch.setattr(chatgpt, "_transport", t)
    monkeypatch.setattr(models, "_transport", t)
    return fake


def test_sign_in_by_pasting_the_address_then_use_the_plan(app, openai):
    url = app.post("/api/chatgpt/start").json()["url"]
    q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
    assert q["client_id"] == "dynamic_agent_client" and q["agent_name_hint"] == "Bamah"
    assert "chatgpt.tokens.use.direct" in q["scope"] and q["code_challenge_method"] == "S256"
    assert q["redirect_uri"].startswith("http://127.0.0.1:") and q["ext_agent_host_id"]
    openai.nonce = q["nonce"]
    # a wrong state is refused
    bad = app.post("/api/chatgpt/finish", json={"url": f"http://127.0.0.1:8465/auth/callback?code=c&state=nope&client_id=oaiapp_123"})
    assert bad.status_code == 400
    ok = app.post("/api/chatgpt/finish", json={"url": f"http://127.0.0.1:8465/auth/callback?code=c&state={q['state']}&client_id=oaiapp_123"})
    assert ok.status_code == 200, ok.text
    assert (chatgpt.config.DATA / "chatgpt.json").stat().st_mode & 0o777 == 0o600
    s = app.get("/api/settings").json()
    assert s["chatgpt"]["email"] == "a@b.c"
    conn = next(c for c in s["connections"] if c["preset"] == "chatgpt")
    assert app.get(f"/api/connections/{conn['id']}/models").json() == [{"id": "gpt-x", "name": "GPT X"}]
    # a second sign-in reuses the issued client id and doesn't register again
    q2 = {k: v[0] for k, v in parse_qs(urlparse(app.post("/api/chatgpt/start").json()["url"]).query).items()}
    assert q2["client_id"] == "oaiapp_123" and "agent_name_hint" not in q2

    # a character played on the plan
    sid = app.post("/api/stories", json={"title": "T", "model": f"{conn['id']}/gpt-x"}).json()["id"]
    mara = app.post("/api/characters", json={"name": "Mara", "story_id": sid}).json()["id"]
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    app.post(f"/api/scenes/{sc}/say", json={"text": "Hello"})
    out = stream(app, f"/api/scenes/{sc}/turn", {"character_id": mara})
    assert out[-1][0] == "done" and out[-1][1]["content"] == "Hi." and out[-1][1]["inner"] == "Calm."

    # refreshing replaces the refresh token
    creds = chatgpt.load()
    creds["expires_at"] = 0
    chatgpt._save(creds)
    import asyncio
    assert asyncio.run(chatgpt.access_token()) == "at-2"
    assert chatgpt.load()["refresh_token"] == "rt-2"

    assert app.post("/api/chatgpt/disconnect").json()["told"] is True
    assert chatgpt.load() is None
