"""Portraits: a picture made from a character's appearance, by whichever image model is picked in Settings.

- OpenRouter: its Image API (/images), asking for the portrait's shape and a modest size from what
  the model takes, as its image model list says.
- OpenAI and Gemini: their images endpoint (/images/generations).
- Other OpenAI-style services, and an OpenRouter model that isn't on its image list: a chat request
  that asks for an image back (modalities: image).
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
    params = None
    if preset == "openrouter":
        headers["x-title"] = config.NAME
        try:
            params = next((m["params"] for m in await models.available(s[0], kind="image") if m["id"] == model), None)
        except ModelError:
            params = None
    try:
        async with models._http(180) as c:
            if params is not None:
                body = {"model": model, "prompt": prompt}
                for key, prefer in (("aspect_ratio", SHAPES), ("resolution", SIZES)):
                    v = _choose(params.get(key), prefer)
                    if v:
                        body[key] = v
                obj = _ok(await c.post(base + "/images", headers=headers, json=body))
                for item in obj.get("data") or []:
                    if item.get("b64_json"):
                        return base64.b64decode(item["b64_json"])
                    if item.get("url"):
                        return (await c.get(item["url"])).content
            elif preset in ("openai", "gemini"):
                r = await c.post(base + "/images/generations", headers=headers,
                                 json={"model": model, "prompt": prompt, "n": 1, "size": "1024x1024"})
                obj = _ok(r)
                item = (obj.get("data") or [{}])[0]
                if item.get("b64_json"):
                    return base64.b64decode(item["b64_json"])
                if item.get("url"):
                    return (await c.get(item["url"])).content
            else:
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


SHAPES = ("4:5", "3:4", "2:3", "1:1")          # portraits are shown 4:5
SIZES = ("1K", "1.5K", "2K", "768", "4K")       # big enough, and the cheapest that is


def _choose(param, prefer) -> str | None:
    """The first of `prefer` the model takes, or None to leave it to the model."""
    if not isinstance(param, dict):
        return None
    values = param.get("values") or []
    return next((v for v in prefer if v in values), None)


def _ok(r: httpx.Response) -> dict:
    if r.status_code >= 400:
        raise ModelError(models._status(r.status_code), models._detail(r.text))
    return r.json()


def save(data: bytes, cid: int | None) -> str:
    kind = "png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "webp" if data[8:12] == b"WEBP" else "jpg"
    name = f"{cid or 'p'}-{secrets.token_hex(5)}.{kind}"
    config.path("avatars", name).write_bytes(data)
    return name
