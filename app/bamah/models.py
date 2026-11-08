"""Talking to the AI models.

Three ways in, so any model can play a character:

- the OpenAI chat format, which nearly every service speaks: OpenRouter, OpenAI, Google Gemini,
  Ollama on your own computer, LM Studio and the like;
- Claude, through Anthropic's own SDK;
- a ChatGPT plan, through "Sign in with ChatGPT" (see chatgpt.py), which speaks the Responses API.

A model is named "connection id/model name", so one setting holds both.
"""

import importlib
import json
import logging
import time

import httpx

from . import chatgpt, config, db

log = logging.getLogger("bamah.models")

PRESETS = {
    "openrouter": {"name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "key": True},
    "openai": {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "key": True},
    "anthropic": {"name": "Claude", "base_url": "", "key": True},
    "gemini": {"name": "Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "key": True},
    "ollama": {"name": "Ollama", "base_url": "http://host.docker.internal:11434/v1", "key": False},
    "custom": {"name": "Other", "base_url": "", "key": False},
    "chatgpt": {"name": "ChatGPT", "base_url": "", "key": False},
}

# Claude models that take the server-side refusal fallback (Haiku doesn't).
CLAUDE_FALLBACK = ("claude-opus", "claude-sonnet", "claude-fable")

_transport = None          # tests swap in an httpx.MockTransport
_model_lists: dict[int, tuple[float, list]] = {}

# Services that play one character themselves rather than take a prompt: preset → async generator.
TURNS: dict = {}


class ModelError(Exception):
    """Something the page can say plainly: code is one of key, model, limit, refused, network, down, setup, request."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def split(ref: str | None) -> tuple[int, str] | None:
    if not ref or "/" not in ref:
        return None
    cid, _, model = ref.partition("/")
    try:
        return int(cid), model
    except ValueError:
        return None


def connection(conn_id: int) -> dict:
    with db.connect() as d:
        c = db.row(d.execute("select * from connection where id = ?", (conn_id,)).fetchone())
    if not c:
        raise ModelError("setup", "that connection is gone")
    return c


def label(ref: str | None) -> str:
    """How a model is shown: "Sonnet 5.5 · OpenRouter" style, kept short."""
    s = split(ref)
    if not s:
        return ""
    try:
        c = connection(s[0])
    except ModelError:
        return s[1]
    return f"{s[1]} · {c['name']}"


def _http(timeout: float = 300) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=20), transport=_transport)


def _status(code: int) -> str:
    return {401: "key", 403: "key", 404: "model", 402: "limit", 429: "limit"}.get(code, "down" if code >= 500 else "request")


async def stream(ref: str, system: str, messages: list[dict], *, effort: str = "medium"):
    """Yield the reply a piece at a time. messages alternate user and assistant, starting with user."""
    s = split(ref)
    if not s:
        raise ModelError("setup", "no model picked")
    conn = connection(s[0])
    model = s[1]
    if conn["preset"] in TURNS:
        raise ModelError("setup", "this connection only plays characters")
    if conn["preset"] == "anthropic":
        gen = _claude(conn, model, system, messages, effort)
    elif conn["preset"] == "chatgpt":
        gen = _chatgpt(conn, model, system, messages)
    else:
        gen = _chat(conn, model, system, messages)
    async for piece in gen:
        yield piece


async def complete(ref: str, system: str, messages: list[dict], *, effort: str = "low") -> str:
    out = []
    async for piece in stream(ref, system, messages, effort=effort):
        out.append(piece)
    return "".join(out)


# --- The OpenAI chat format -------------------------------------------------------------------

async def _chat(conn, model, system, messages):
    base = (conn["base_url"] or "").rstrip("/")
    if not base:
        raise ModelError("setup", "this connection has no address")
    headers = {"content-type": "application/json"}
    if conn["api_key"]:
        headers["authorization"] = f"Bearer {conn['api_key']}"
    if conn["preset"] == "openrouter":
        headers["x-title"] = config.NAME
    body = {"model": model, "stream": True, "messages": [{"role": "system", "content": system}] + messages}
    try:
        async with _http() as c, c.stream("POST", base + "/chat/completions", headers=headers, json=body) as r:
            if r.status_code >= 400:
                text = (await r.aread()).decode(errors="replace")
                log.warning("chat %s %s: %s", conn["preset"], r.status_code, text[:300])
                raise ModelError(_status(r.status_code), _detail(text))
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except ValueError:
                    continue
                if obj.get("error"):
                    raise ModelError("refused" if "moderation" in json.dumps(obj["error"]).lower() else "down",
                                     _detail(json.dumps(obj["error"])))
                for ch in obj.get("choices") or []:
                    piece = (ch.get("delta") or {}).get("content")
                    if piece:
                        yield piece
                    if ch.get("finish_reason") == "content_filter":
                        raise ModelError("refused", "the provider's filter stopped it")
    except httpx.TransportError as e:
        raise ModelError("network", str(e)) from e


def _detail(text: str) -> str:
    try:
        obj = json.loads(text)
        err = obj.get("error", obj)
        if isinstance(err, dict):
            return str(err.get("message") or err)[:300]
        return str(err)[:300]
    except ValueError:
        return text[:300]


# --- Claude -----------------------------------------------------------------------------------

async def _claude(conn, model, system, messages, effort):
    import anthropic

    if not conn["api_key"]:
        raise ModelError("key", "no key")
    client = anthropic.AsyncAnthropic(api_key=conn["api_key"], max_retries=2)
    extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"} if model.startswith(CLAUDE_FALLBACK) else {}
    try:
        async with client.beta.messages.stream(
                model=model, max_tokens=16000,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=messages, cache_control={"type": "ephemeral"},
                output_config={"effort": effort}, **extra) as s:
            async for ev in s:
                if ev.type == "text":
                    yield ev.text
            msg = await s.get_final_message()
        if msg.stop_reason == "refusal":
            raise ModelError("refused", "Claude declined")
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
        raise ModelError("key", e.message) from e
    except anthropic.NotFoundError as e:
        raise ModelError("model", e.message) from e
    except anthropic.RateLimitError as e:
        raise ModelError("limit", e.message) from e
    except anthropic.BadRequestError as e:
        raise ModelError("limit" if "credit" in (e.message or "").lower() else "request", e.message) from e
    except anthropic.APIStatusError as e:
        raise ModelError("down", e.message) from e
    except anthropic.APIConnectionError as e:
        raise ModelError("network", str(e)) from e


# --- A ChatGPT plan (Responses API) ---------------------------------------------------------

async def _chatgpt(conn, model, system, messages):
    for attempt in (1, 2):
        token = await chatgpt.access_token(force=attempt == 2)
        body = {"model": model, "instructions": system, "store": False, "stream": True,
                "input": [{"role": m["role"], "content": m["content"]} for m in messages]}
        headers = {"authorization": f"Bearer {token}", "content-type": "application/json"}
        got_any, done = False, False
        try:
            async with _http() as c, c.stream("POST", chatgpt.RESOURCE + "/responses", headers=headers, json=body) as r:
                if r.status_code == 401 and attempt == 1:
                    continue
                if r.status_code >= 400:
                    text = (await r.aread()).decode(errors="replace")
                    log.warning("chatgpt %s: %s", r.status_code, text[:300])
                    code = "limit" if "usage" in text and r.status_code == 429 else _status(r.status_code)
                    raise ModelError(code, _detail(text))
                async for line in r.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        obj = json.loads(line[5:].strip())
                    except ValueError:
                        continue
                    kind = obj.get("type", "")
                    if kind == "response.output_text.delta":
                        got_any = True
                        yield obj.get("delta", "")
                    elif kind == "response.completed":
                        done = True
                    elif kind == "response.failed":
                        err = (obj.get("response") or {}).get("error") or {}
                        code = err.get("code", "")
                        raise ModelError("limit" if code.startswith("subscription_sharing") else "down",
                                         err.get("message", code))
                    elif kind == "response.incomplete":
                        done = got_any
                        if not got_any:
                            raise ModelError("refused", "the reply came back incomplete")
        except httpx.TransportError as e:
            raise ModelError("network", str(e)) from e
        if not done:
            raise ModelError("down", "the reply stopped before it finished")
        return


# --- Listing what a connection offers ---------------------------------------------------------

async def available(conn_id: int, fresh: bool = False) -> list[dict]:
    """[{"id", "name"}] for the model picker, kept for an hour."""
    hit = _model_lists.get(conn_id)
    if hit and not fresh and time.time() - hit[0] < 3600:
        return hit[1]
    conn = connection(conn_id)
    out: list[dict] = []
    if conn["preset"] in TURNS:
        return []
    if conn["preset"] == "anthropic":
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=conn["api_key"], max_retries=1)
        try:
            async for m in client.models.list(limit=100):
                out.append({"id": m.id, "name": m.display_name or m.id})
        except anthropic.APIError as e:
            raise ModelError("key", str(e)) from e
    elif conn["preset"] == "chatgpt":
        token = await chatgpt.access_token()
        async with _http(30) as c:
            r = await c.get(chatgpt.RESOURCE + "/models", headers={"authorization": f"Bearer {token}"})
        if r.status_code >= 400:
            raise ModelError(_status(r.status_code), _detail(r.text))
        obj = r.json()
        for m in obj.get("models") or []:
            if m.get("visibility", "list") == "list" and m.get("slug"):
                out.append({"id": m["slug"], "name": m.get("display_name") or m["slug"]})
        for m in obj.get("data") or []:
            out.append({"id": m["id"], "name": m["id"]})
    else:
        base = (conn["base_url"] or "").rstrip("/")
        headers = {"authorization": f"Bearer {conn['api_key']}"} if conn["api_key"] else {}
        try:
            async with _http(30) as c:
                r = await c.get(base + "/models", headers=headers)
        except httpx.TransportError as e:
            raise ModelError("network", str(e)) from e
        if r.status_code >= 400:
            raise ModelError(_status(r.status_code), _detail(r.text))
        for m in r.json().get("data") or []:
            mid = m.get("id", "")
            if mid.startswith("models/"):            # Gemini's names
                mid = mid[7:]
            out.append({"id": mid, "name": m.get("name") or mid})
        out.sort(key=lambda m: m["id"])
    _model_lists[conn_id] = (time.time(), out)
    return out


def forget(conn_id: int):
    _model_lists.pop(conn_id, None)


# Private add-ons that live only on one server (git ignores bamah/extras). They register their own
# presets, and services that play a character themselves, in PRESETS and TURNS.
try:
    importlib.import_module(__package__ + ".extras")
except ModuleNotFoundError as e:
    if e.name != __package__ + ".extras":   # a missing folder is fine; a broken add-on isn't
        raise
