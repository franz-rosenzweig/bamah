import asyncio
import json

import httpx

from bamah import models
from tests.conftest import FakeModel

LISTED = [
    {"id": "glm", "name": "GLM", "reasoning": {"mandatory": True, "supported_efforts": ["max", "high", "low"], "default_effort": "max"}},
    {"id": "kimi", "name": "Kimi", "reasoning": {"mandatory": False, "supported_efforts": ["max", "high", "low", "none"]}},
    {"id": "argon", "name": "Argon", "reasoning": {"mandatory": True, "supported_efforts": ["high", "medium", "low"]}},
    {"id": "qwen", "name": "Qwen", "reasoning": {"mandatory": False, "supports_max_tokens": True}},
    {"id": "plain", "name": "Plain"},
    {"id": "openrouter/auto", "name": "Auto", "supported_parameters": ["reasoning"]},
]


class Router(FakeModel):
    """OpenRouter as Bamah sees it: a model list that says how each one thinks, and a chat that
    turns down a thinking level the model doesn't take."""

    def __call__(self, request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": LISTED})
        body = json.loads(request.content)
        if body.get("model") == "picky" and "reasoning" in body:
            self.requests.append(body)
            return httpx.Response(400, json={"error": {"message": "Reasoning is mandatory for this endpoint and cannot be disabled."}})
        return super().__call__(request)


def router(app, monkeypatch):
    fake = Router()
    monkeypatch.setattr(models, "_transport", httpx.MockTransport(fake))
    models._model_lists.clear()
    cid = app.post("/api/connections", json={"preset": "openrouter", "base_url": "http://router/api/v1", "api_key": "sk-test"}).json()["id"]
    return fake, cid


def ask(cid, model, effort="medium"):
    return asyncio.run(models.complete(f"{cid}/{model}", "Say hi", [{"role": "user", "content": "hi"}], effort=effort))


def test_nearest_level():
    glm = LISTED[0]["reasoning"]
    assert models.nearest(glm, "none") == "low"          # can't switch off, so the least it does
    assert models.nearest(glm, "low") == "low"
    assert models.nearest(glm, "high") == "high"
    assert models.nearest(LISTED[1]["reasoning"], "none") == "none"
    assert models.nearest({"supported_efforts": ["xhigh", "high", "medium"]}, "low") == "medium"
    assert models.nearest({"supported_efforts": ["minimal", "low"]}, "high") == "low"
    assert models.nearest({"mandatory": True}, "none") == "low"
    assert models.nearest({}, "none") == "none"


def test_thinking_goes_with_openrouter(app, monkeypatch):
    fake, cid = router(app, monkeypatch)
    assert app.get("/api/settings").json()["settings"]["thinking"] == "low"
    for m in ("glm", "kimi", "plain", "qwen", "openrouter/auto", "unlisted"):
        ask(cid, m)
    sent = {r["model"]: r.get("reasoning") for r in fake.requests}
    assert sent == {"glm": {"effort": "low"}, "kimi": {"effort": "low"}, "plain": None, "qwen": {"effort": "low"},
                    "openrouter/auto": {"effort": "low"}, "unlisted": {"effort": "low"}}

    app.put("/api/settings", json={"thinking": "off"})
    fake.requests.clear()
    for m in ("glm", "kimi", "argon"):
        ask(cid, m)
    assert [r["reasoning"] for r in fake.requests] == [{"effort": "low"}, {"effort": "none"}, {"effort": "low"}]

    app.put("/api/settings", json={"thinking": "high"})
    fake.requests.clear()
    ask(cid, "kimi")                    # a character's line
    ask(cid, "kimi", effort="low")      # the bookkeeping never thinks more than low
    assert [r["reasoning"] for r in fake.requests] == [{"effort": "high"}, {"effort": "low"}]


def test_turned_down_asks_again_without_it(app, monkeypatch):
    fake, cid = router(app, monkeypatch)
    assert ask(cid, "picky") == "ready"
    assert ["reasoning" in r for r in fake.requests] == [True, False]


def test_other_services_get_nothing_new(app):
    ask(app.conn, "fake-small")
    assert "reasoning" not in app.fake.requests[-1]
