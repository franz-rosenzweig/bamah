import base64

from bamah import config
from tests.test_scenes import setup_story

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def upload(app, sc, data=PNG, kind="image/png"):
    return app.post(f"/api/scenes/{sc}/background", files={"file": ("wall.png", data, kind)})


def test_a_scene_background(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"title": "Dinner", "characters": [mara, ben]}).json()["id"]
    assert app.get(f"/api/scenes/{sc}").json()["background"] == ""

    first = upload(app, sc).json()["background"]
    assert first.endswith(".png") and app.get(f"/api/scenes/{sc}").json()["background"] == first
    assert app.get(f"/backgrounds/{first}").content == PNG

    # a new one takes its place, and the old file goes
    second = upload(app, sc).json()["background"]
    assert second != first and app.get(f"/backgrounds/{first}").status_code == 404
    assert config.path("backgrounds", second).exists()

    # only pictures
    assert upload(app, sc, b"not a picture", "text/plain").status_code == 400
    assert upload(app, 9999).status_code == 404

    app.delete(f"/api/scenes/{sc}/background")
    assert app.get(f"/api/scenes/{sc}").json()["background"] == ""
    assert not config.path("backgrounds", second).exists()

    # deleting the scene takes its background with it
    third = upload(app, sc).json()["background"]
    app.delete(f"/api/scenes/{sc}")
    assert not config.path("backgrounds", third).exists()
