import io
import json
import time
import zipfile

from bamah import db, engine

from .conftest import stream
from .test_scenes import say, setup_story, turn


def sys_of(app, name):
    return app.fake.prompts_for(name)[-1]["messages"][0]["content"]


def tail_of(app, name):
    return app.fake.prompts_for(name)[-1]["messages"][-1]["content"]


def test_pronouns_appearance_voice_and_style(app):
    sid, mara, ben, cleo = setup_story(app)
    app.patch(f"/api/characters/{mara}", json={"pronouns": "she/her", "appearance": "Red hair she cuts herself."})
    app.patch(f"/api/characters/{ben}", json={"pronouns": "he/him", "appearance": "Tall. Expensive shoes, scuffed."})
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara, ben]}).json()["id"]
    say(app, sc, "Well?")
    turn(app, sc, mara)
    s = sys_of(app, "Mara")
    assert "# Mara (she/her)" in s and "What Mara looks like\nRed hair she cuts herself." in s
    assert "in the first person" in s                     # the default voice is "I"
    assert "Ben Ortiz (he/him; Tall. Expensive shoes, scuffed.)" in tail_of(app, "Mara")
    # third person and a style of her own, for one character only
    app.patch(f"/api/characters/{mara}", json={"person": "third", "style": "narrative"})
    turn(app, sc, mara)
    s = sys_of(app, "Mara")
    assert "in the third person (she/her)" in s and "novel prose" in s
    turn(app, sc, ben)
    assert "in the first person" in sys_of(app, "Ben Ortiz") and "roleplay" in sys_of(app, "Ben Ortiz")


def test_personas_join_stories_and_tie_to_characters(app):
    sid, mara, ben, cleo = setup_story(app)
    nate = app.post("/api/personas", json={"name": "Nate", "pronouns": "he/him", "about": "A regular at the café."}).json()["id"]
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    say(app, sc, "Morning, Mara.", as_="Nate")
    assert app.get(f"/api/stories/{sid}").json()["personas"] == [nate]
    turn(app, sc, mara)
    assert "- Nate (he/him): A regular at the café." in sys_of(app, "Mara")
    assert "Here with Mara: Nate." in tail_of(app, "Mara")
    app.patch(f"/api/characters/{mara}", json={"persona_id": nate})
    turn(app, sc, mara)
    assert "The writer usually plays Nate opposite Mara." in sys_of(app, "Mara")
    app.delete(f"/api/personas/{nate}")
    assert app.get(f"/api/stories/{sid}").json()["personas"] == []


def test_old_story_roles_become_personas(app):
    sid = app.post("/api/stories", json={"title": "Old"}).json()["id"]
    with db.connect() as d:
        d.execute("update story set roles = ? where id = ?", (json.dumps([{"name": "Aunt Odile", "about": "The hostess."}]), sid))
    db.init()
    people = app.get("/api/personas").json()
    assert [p["name"] for p in people] == ["Aunt Odile"]
    assert app.get(f"/api/stories/{sid}").json()["personas"] == [people[0]["id"]]


def test_what_if_scenes_leave_nothing_until_they_count(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"title": "What if", "whatif": True, "characters": [mara, ben]}).json()["id"]
    say(app, sc, "Mara finds the letter first.")
    turn(app, sc, mara)
    time.sleep(0.3)
    app.post(f"/api/scenes/{sc}/end")
    story = app.get(f"/api/stories/{sid}").json()
    assert story["feelings"] == {} and story["scenes"][0]["whatif"] == 1
    assert app.get(f"/api/characters/{mara}").json()["stories"][0]["memories"] == []
    # another scene doesn't pull it into memory either
    sc2 = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    say(app, sc2, "Next morning.")
    turn(app, sc2, mara)
    assert app.get(f"/api/characters/{mara}").json()["stories"][0]["memories"] == []
    # made to count: now it's remembered like any scene
    app.patch(f"/api/scenes/{sc}", json={"whatif": False})
    turn(app, sc2, mara)
    assert any(m["scene_id"] == sc for m in app.get(f"/api/characters/{mara}").json()["stories"][0]["memories"])


def test_repetition_guard_names_the_tics():
    lines = ["I swear to god, Ben, you never listen.", "Fine. I swear to god this is the last time.",
             "I swear to god I'll scream.", "Whatever you say."]
    assert "i swear to god" in engine.repeated(lines)[0]
    assert engine.repeated(["All different.", "Nothing alike here.", "Not one bit."]) == []


def test_repetition_guard_in_the_prompt(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    for _ in range(3):
        say(app, sc, "And?")
        turn(app, sc, mara)
    assert "Mara has been leaning on these lately" in tail_of(app, "Mara")
    app.put("/api/settings", json={"repetition": "0"})
    turn(app, sc, mara)
    assert "leaning on these" not in tail_of(app, "Mara")


def test_draft_and_suggest(app):
    sid, mara, ben, cleo = setup_story(app)
    out = app.post(f"/api/characters/{mara}/draft", json={"words": "sad, fun, bubbly"}).json()
    assert out["pronouns"] == "she/her" and out["key_memories"] == "Bet $50\nHates cinnamon"
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    assert app.post(f"/api/scenes/{sc}/suggest", json={}).json()["text"] == "The lights flicker."


def _docx(text: str) -> bytes:
    xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in text.split("\n")) + "</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


def test_bring_in_files(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    r = app.post("/api/import", data={"target": "scene", "target_id": str(sc)},
                 files={"file": ("Chapter 3.docx", _docx("The rain started at noon.\nNobody came."), "application/octet-stream")})
    assert r.status_code == 200 and r.json()["words"] == 7
    turn(app, sc, mara)
    everything = "\n".join(m["content"] for m in app.fake.prompts_for("Mara")[-1]["messages"])
    assert "[A document everyone here has read, “Chapter 3.docx”:]\nThe rain started at noon.\n\nNobody came." in everything
    app.post("/api/import", data={"target": "character", "target_id": str(mara)},
             files={"file": ("backstory.txt", b"Born in Lyon.", "text/plain")})
    assert app.get(f"/api/characters/{mara}").json()["journal"][0]["text"] == "Born in Lyon."
    bad = app.post("/api/import", data={"target": "story", "target_id": str(sid)}, files={"file": ("x.exe", b"MZ", "x")})
    assert bad.status_code == 415


def test_portraits(app):
    sid, mara, ben, cleo = setup_story(app)
    app.patch(f"/api/characters/{mara}", json={"appearance": "Red hair."})
    assert app.post(f"/api/characters/{mara}/portraits", json={"style": "anime"}).status_code == 502   # no model yet
    app.put("/api/settings", json={"portrait_model": f"{app.conn}/fake-image"})
    p = app.post(f"/api/characters/{mara}/portraits", json={"style": "anime"}).json()
    assert p["file"].endswith(".png") and "Red hair." in p["prompt"] and "anime" in p["prompt"]
    assert app.get(f"/api/characters/{mara}").json()["avatar"] == p["file"]
    assert app.get(f"/avatars/{p['file']}").status_code == 200
    # reuse it for someone else, then delete: the file stays while it's in use
    app.post(f"/api/characters/{ben}/portrait", json={"portrait_id": p["id"]})
    app.delete(f"/api/portraits/{p['id']}")
    assert app.get(f"/avatars/{p['file']}").status_code == 200
    assert app.get("/api/portraits").json() == []
