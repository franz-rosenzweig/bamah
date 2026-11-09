import base64
import json

import httpx

from bamah import images, models

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

IMAGE_MODELS = [
    {"id": "bfl/flux", "name": "FLUX", "supported_parameters": {
        "resolution": {"type": "enum", "values": ["768", "1K", "2K"]},
        "aspect_ratio": {"type": "enum", "values": ["1:1", "4:5", "16:9"]}}},
    {"id": "seed/dream", "name": "Dream", "supported_parameters": {
        "resolution": {"type": "enum", "values": ["2K", "4K"]},
        "aspect_ratio": {"type": "enum", "values": ["1:1", "3:4"]}}},
    {"id": "meta/plain", "name": "Plain"},
]


class Router:
    """OpenRouter's Image API: a list of image models with what each takes, and /images."""

    def __init__(self):
        self.requests = []

    def __call__(self, request):
        path = request.url.path
        if path.endswith("/images/models"):
            return httpx.Response(200, json={"data": IMAGE_MODELS})
        if path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "z/glm", "name": "GLM"}]})
        body = json.loads(request.content)
        self.requests.append((path, body))
        if path.endswith("/images"):
            return httpx.Response(200, json={"created": 1, "data": [{"b64_json": PNG, "media_type": "image/png"}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "", "images": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{PNG}"}}]}}]})


def router(app, monkeypatch):
    fake = Router()
    monkeypatch.setattr(models, "_transport", httpx.MockTransport(fake))
    models._model_lists.clear()
    cid = app.post("/api/connections", json={"preset": "openrouter", "base_url": "http://router/api/v1", "api_key": "sk-test"}).json()["id"]
    return fake, cid


def test_choosing_shape_and_size():
    flux, dream = IMAGE_MODELS[0]["supported_parameters"], IMAGE_MODELS[1]["supported_parameters"]
    assert images._choose(flux["aspect_ratio"], images.SHAPES) == "4:5"
    assert images._choose(flux["resolution"], images.SIZES) == "1K"
    assert images._choose(dream["aspect_ratio"], images.SHAPES) == "3:4"
    assert images._choose(dream["resolution"], images.SIZES) == "2K"
    assert images._choose(None, images.SHAPES) is None


def test_openrouter_lists_and_paints(app, monkeypatch):
    fake, cid = router(app, monkeypatch)
    listed = app.get(f"/api/connections/{cid}/models?kind=image").json()
    assert [m["id"] for m in listed] == ["seed/dream", "bfl/flux", "meta/plain"]
    assert [m["id"] for m in app.get(f"/api/connections/{cid}/models").json()] == ["z/glm"]

    ch = app.post("/api/characters", json={"name": "Mara"}).json()["id"]
    for model, sent in (("bfl/flux", {"aspect_ratio": "4:5", "resolution": "1K"}),
                        ("seed/dream", {"aspect_ratio": "3:4", "resolution": "2K"}),
                        ("meta/plain", {})):
        app.put("/api/settings", json={"portrait_model": f"{cid}/{model}"})
        p = app.post(f"/api/characters/{ch}/portraits", json={"style": "painted"}).json()
        assert p["file"].endswith(".png")
        path, body = fake.requests[-1]
        assert path.endswith("/images") and body["model"] == model and "Mara" in body["prompt"]
        assert {k: v for k, v in body.items() if k in ("aspect_ratio", "resolution")} == sent

    # a model that isn't on the image list still goes the old way, through a chat
    app.put("/api/settings", json={"portrait_model": f"{cid}/google/some-chat-image"})
    assert app.post(f"/api/characters/{ch}/portraits", json={}).status_code == 200
    path, body = fake.requests[-1]
    assert path.endswith("/chat/completions") and body["modalities"] == ["image", "text"]
    assert base64.b64decode(PNG)[:4] == b"\x89PNG"


def test_who_can_draw(app, monkeypatch):
    presets = app.get("/api/settings").json()["presets"]
    assert presets["openrouter"]["draws"] and not presets["anthropic"]["draws"] and not presets["chatgpt"]["draws"]
