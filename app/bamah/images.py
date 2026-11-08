"""Portraits: a picture made from a character's appearance, by whichever image model is picked in Settings.

- OpenAI and Gemini: their images endpoint (/images/generations).
- OpenRouter and other OpenAI-style services: a chat request that asks for an image back
  (modalities: image), which is how OpenRouter serves its image models.
"""

import base64
import secrets

import httpx

from . import config, models
from .models import ModelError

STYLES = {
    "photo": "a natural photographic portrait, soft window light, shallow depth of field",
    "painted": "a painted portrait, like the art on a literary novel's cover, visible brushwork",
    "anime": "an anime-style character portrait, clean line art, soft shading",
}


def prompt_for(ch: dict, style: str, description: str | None = None) -> str:
    who = ch["name"] + (f" ({ch['pronouns']})" if ch.get("pronouns") else "")
    looks = (description or ch.get("appearance") or "").strip() or "someone with an expressive, memorable face"
    return (f"A head-and-shoulders portrait of {who}, a character in a novel. {looks} "
            f"Style: {STYLES.get(style, STYLES['painted'])}. A plain, softly lit background. No text, no lettering, no frame.")


async def generate(ref: str, prompt: str) -> bytes:
    s = models.split(ref)
    if not s:
        raise ModelError("setup", "no portrait model picked")
    conn = models.connection(s[0])
    model = s[1]
    preset = conn["preset"]
    if preset in ("anthropic", "chatgpt") or preset in models.TURNS:
        raise ModelError("setup", "this connection can't make pictures")
    base = (conn["base_url"] or "").rstrip("/")
    headers = {"content-type": "application/json"}
    if conn["api_key"]:
        headers["authorization"] = f"Bearer {conn['api_key']}"
    try:
        async with models._http(180) as c:
            if preset in ("openai", "gemini"):
                r = await c.post(base + "/images/generations", headers=headers,
                                 json={"model": model, "prompt": prompt, "n": 1, "size": "1024x1024"})
                obj = _ok(r)
                item = (obj.get("data") or [{}])[0]
                if item.get("b64_json"):
                    return base64.b64decode(item["b64_json"])
                if item.get("url"):
                    return (await c.get(item["url"])).content
            else:
                if preset == "openrouter":
                    headers["x-title"] = config.NAME
                r = await c.post(base + "/chat/completions", headers=headers,
                                 json={"model": model, "modalities": ["image", "text"],
                                       "messages": [{"role": "user", "content": prompt}]})
                obj = _ok(r)
                msg = ((obj.get("choices") or [{}])[0].get("message") or {})
                for img in msg.get("images") or []:
                    url = (img.get("image_url") or {}).get("url", "")
                    if url.startswith("data:"):
                        return base64.b64decode(url.split(",", 1)[1])
                    if url:
                        return (await c.get(url)).content
    except httpx.TransportError as e:
        raise ModelError("network", str(e)) from e
    raise ModelError("empty", "no picture came back")


def _ok(r: httpx.Response) -> dict:
    if r.status_code >= 400:
        raise ModelError(models._status(r.status_code), models._detail(r.text))
    return r.json()


def save(data: bytes, cid: int | None) -> str:
    kind = "png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "webp" if data[8:12] == b"WEBP" else "jpg"
    name = f"{cid or 'p'}-{secrets.token_hex(5)}.{kind}"
    config.path("avatars", name).write_bytes(data)
    return name
