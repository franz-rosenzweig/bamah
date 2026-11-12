from bamah import config, db

from .test_scenes import say, setup_story, turn


def test_deleting_a_story_takes_its_scenes_memories_and_backgrounds(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara, ben]}).json()["id"]
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    bg = app.post(f"/api/scenes/{sc}/background", files={"file": ("bg.png", png, "image/png")}).json()["background"]
    say(app, sc, "Ben, where were you?")
    turn(app, sc, ben)
    assert config.path("backgrounds", bg).exists()
    assert app.delete(f"/api/stories/{sid}").status_code == 200
    assert app.get(f"/api/stories/{sid}").status_code == 404
    assert app.get(f"/api/scenes/{sc}").status_code == 404
    with db.connect() as d:
        assert d.execute("select count(*) from event").fetchone()[0] == 0
        assert d.execute("select count(*) from memory where story_id = ?", (sid,)).fetchone()[0] == 0
    assert not config.path("backgrounds", bg).exists()
    assert {c["id"] for c in app.get("/api/characters").json()} == {mara, ben, cleo}     # characters stay


def test_deleting_a_scene_leaves_the_story(app):
    sid, mara, ben, cleo = setup_story(app)
    one = app.post(f"/api/stories/{sid}/scenes", json={"title": "One", "characters": [mara, ben]}).json()["id"]
    two = app.post(f"/api/stories/{sid}/scenes", json={"title": "Two", "characters": [mara]}).json()["id"]
    assert app.delete(f"/api/scenes/{one}").status_code == 200
    assert [x["id"] for x in app.get(f"/api/stories/{sid}").json()["scenes"]] == [two]


def test_after_a_character_is_deleted_their_scenes_still_open_and_play(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara, ben]}).json()["id"]
    say(app, sc, "Ben, where were you?")
    turn(app, sc, ben)
    assert app.delete(f"/api/characters/{ben}").status_code == 200
    s = app.get(f"/api/scenes/{sc}").json()
    assert ben not in [c["id"] for c in s["cast"]] and ben not in s["here"]
    say(app, sc, "Mara, what do you think?")
    out = turn(app, sc, mara)
    assert any(k == "done" for k, _ in out), out[-3:]
