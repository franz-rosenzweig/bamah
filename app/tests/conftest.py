import json
import re

import httpx
import pytest


class FakeModel:
    """An OpenAI-style chat service that answers by what it was asked to do, and remembers every request."""

    def __init__(self):
        self.requests = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "fake-small"}, {"id": "fake-large"}]})
        body = json.loads(request.content)
        self.requests.append(body)
        if body.get("modalities"):
            png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            return httpx.Response(200, json={"choices": [{"message": {"content": "", "images": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png}"}}]}}]})
        system = body["messages"][0]["content"]
        last = body["messages"][-1]["content"]
        if system.startswith("You help a novelist sketch"):
            text = json.dumps({"pronouns": "she/her", "appearance": "Red hair.", "personality": "Works mornings.",
                               "inner_life": "Wants to be noticed.", "voice": "Fast.", "key_memories": ["Bet $50", "Hates cinnamon"]})
        elif system.startswith("You help a novelist keep a scene moving"):
            text = "The lights flicker."
        elif system.startswith("You are playing"):
            name = re.match(r"You are playing (.+?) in a story", system).group(1)
            if "Continue" in last.splitlines()[-1]:
                text = "And another thing."
            else:
                text = f"<inner>{name} is annoyed and hiding it.</inner>{name}: Hello from {name}, about Paris."
        elif system.startswith("You keep the memory"):
            name = re.match(r"You keep the memory of (.+?), a character", system).group(1)
            text = f"- {name} remembered the argument about Paris.\n- {name} saw who was there."
        elif system.startswith("You keep") and "running notes" in system:
            text = "Relationships and growth\nWary.\nImportant facts\nParis.\nOngoing threads\nThe letter."
        elif system.startswith("You keep track of how"):
            people = re.search(r"People in the story: (.*)", last).group(1).split(", ")
            text = json.dumps({"mood": "prickly", "toward": {p: "doesn't trust them" for p in people if p}})
        elif system.startswith("You run the turn order"):
            names = re.findall(r"^- ([^:]+):", last, re.M)
            text = ", ".join(reversed(names))
        else:
            text = "ready"
        chunks = [text[i:i + 7] for i in range(0, len(text), 7)]
        sse = "".join(f"data: {json.dumps({'choices': [{'delta': {'content': c}}]})}\n\n" for c in chunks) + "data: [DONE]\n\n"
        return httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})

    def prompts_for(self, name):
        return [r for r in self.requests if r["messages"][0]["content"].startswith(f"You are playing {name} ")]


@pytest.fixture
def app(tmp_path, monkeypatch):
    from bamah import config, models
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "PASSWORD", "")
    fake = FakeModel()
    monkeypatch.setattr(models, "_transport", httpx.MockTransport(fake))
    models._model_lists.clear()
    from fastapi.testclient import TestClient
    from bamah.web import app as web
    with TestClient(web) as client:
        client.fake = fake
        cid = client.post("/api/connections", json={"preset": "custom", "base_url": "http://fake/v1", "model": "fake-small"}).json()["id"]
        client.conn = cid
        yield client


def stream(client, url, body=None):
    """Post to an SSE endpoint and return [(event, data)]."""
    out = []
    with client.stream("POST", url, json=body or {}) as r:
        kind = None
        for ln in r.iter_lines():
            if ln.startswith("event: "):
                kind = ln[7:]
            elif ln.startswith("data: "):
                out.append((kind, json.loads(ln[6:])))
    return out
