import time

from bamah import engine

from .conftest import stream


def setup_story(app, **story):
    sid = app.post("/api/stories", json={"title": "The Letter", "premise": "A family in Lyon.", **story}).json()["id"]
    mara = app.post("/api/characters", json={"name": "Mara", "personality": "Proud. Never apologizes first.", "story_id": sid}).json()["id"]
    ben = app.post("/api/characters", json={"name": "Ben Ortiz", "personality": "Charming liar.", "story_id": sid}).json()["id"]
    cleo = app.post("/api/characters", json={"name": "Cleo", "personality": "Quiet, notices everything.", "story_id": sid}).json()["id"]
    return sid, mara, ben, cleo


def say(app, scene, text, as_=""):
    return app.post(f"/api/scenes/{scene}/say", json={"text": text, "as": as_}).json()


def turn(app, scene, cid, **kw):
    return stream(app, f"/api/scenes/{scene}/turn", {"character_id": cid, **kw})


def test_turn_streams_inner_and_text_separately(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"title": "Dinner", "setting": "The kitchen", "characters": [mara, ben]}).json()["id"]
    say(app, sc, "Ben, where were you last night?")
    out = turn(app, sc, ben)
    kinds = [k for k, _ in out]
    assert "inner" in kinds and "text" in kinds and kinds[-1] == "done"
    text = "".join(d for k, d in out if k == "text")
    assert text == "Hello from Ben Ortiz, about Paris."          # the stray "Ben Ortiz:" is gone
    ev = out[-1][1]
    assert ev["inner"] == "Ben Ortiz is annoyed and hiding it."
    assert ev["witnesses"] == [mara, ben]
    assert ev["model_label"].startswith("fake-small")
    # what Ben was given: his sheet, the story, the scene, and her line
    p = app.fake.prompts_for("Ben Ortiz")[-1]
    assert "Charming liar." in p["messages"][0]["content"]
    assert "The kitchen" in p["messages"][0]["content"]
    assert "[Narrator] Ben, where were you last night?" in p["messages"][-1]["content"]
    assert "Write Ben Ortiz's next turn." in p["messages"][-1]["content"]


def test_mentions_pick_who_answers(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara, ben, cleo]}).json()["id"]
    say(app, sc, "@Cleo, and you, Mara?")
    assert app.post(f"/api/scenes/{sc}/next", json={}).json()["speakers"] == [cleo, mara]
    say(app, sc, "Well?")
    # nobody named: the helper decides (the fake picks in reverse order)
    assert app.post(f"/api/scenes/{sc}/next", json={}).json()["speakers"] == [cleo, ben, mara]


def test_they_only_know_what_they_saw_and_memory_follows_them(app):
    sid, mara, ben, cleo = setup_story(app)
    sc1 = app.post(f"/api/stories/{sid}/scenes", json={"title": "Dinner", "characters": [mara, ben]}).json()["id"]
    say(app, sc1, "The letter is from Paris. Burn it.")
    turn(app, sc1, mara)
    # Cleo walks in later: she didn't hear about the letter
    app.post(f"/api/scenes/{sc1}/presence", json={"character_id": cleo, "here": True})
    say(app, sc1, "Cleo, sit down.")
    turn(app, sc1, cleo)
    cleo_prompt = app.fake.prompts_for("Cleo")[-1]
    everything = "\n".join(m["content"] for m in cleo_prompt["messages"])
    assert "Burn it" not in everything
    assert "[Cleo comes in.]" in everything
    assert "only knows what they've seen" in cleo_prompt["messages"][0]["content"]

    # Mara moves to a new scene with Cleo; Ben stays behind
    sc2 = app.post(f"/api/stories/{sid}/scenes", json={"title": "Garden", "characters": [mara, cleo], "from_scene": sc1}).json()["id"]
    detail = app.get(f"/api/scenes/{sc1}").json()
    assert detail["here"] == [ben]
    # Mara's memory of the dinner was written when she left, and comes along into the garden
    say(app, sc2, "Mara, what was in that letter?")
    turn(app, sc2, mara)
    mara_prompt = app.fake.prompts_for("Mara")[-1]["messages"][0]["content"]
    assert "(Dinner) Mara remembered the argument about Paris." in mara_prompt
    assert "Relationships and growth" in mara_prompt            # her running notes for the story
    ch = app.get(f"/api/characters/{mara}").json()
    assert any(m["scene_id"] == sc1 for m in ch["stories"][0]["memories"])


def test_shared_story_everyone_knows(app):
    sid, mara, ben, cleo = setup_story(app, memory="shared")
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    say(app, sc, "The letter is from Paris. Burn it.")
    app.post(f"/api/scenes/{sc}/presence", json={"character_id": cleo, "here": True})
    turn(app, sc, cleo)
    everything = "\n".join(m["content"] for m in app.fake.prompts_for("Cleo")[-1]["messages"])
    assert "Burn it" in everything


def test_corrections_redo_versions_and_examples(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    say(app, sc, "Say sorry, Mara.")
    ev = turn(app, sc, mara)[-1][1]
    # thumbs down with a note she wants kept: it becomes one of Mara's corrections, and the line is taken again
    out = stream(app, f"/api/events/{ev['id']}/redo", {"note": "She'd never apologize first.", "save": True})
    again = out[-1][1]
    assert len(again["versions"]) == 2 and again["pick"] == 1
    sys = app.fake.prompts_for("Mara")[-1]["messages"][0]["content"]
    assert "- She'd never apologize first." in sys
    # a one-off note isn't kept
    stream(app, f"/api/events/{ev['id']}/redo", {"note": "Angrier this time."})
    assert "The writer's note for this turn: Angrier this time." in app.fake.prompts_for("Mara")[-1]["messages"][-1]["content"]
    ch = app.get(f"/api/characters/{mara}").json()
    assert [c["text"] for c in ch["corrections"]] == ["She'd never apologize first."]
    # back to the first take, and a thumbs up keeps it as a line that sounded right
    app.post(f"/api/events/{ev['id']}/pick", json={"index": 0})
    app.post(f"/api/events/{ev['id']}/rate", json={"value": 1})
    turn(app, sc, mara)
    assert "Lines of Mara's that sounded exactly right" in app.fake.prompts_for("Mara")[-1]["messages"][0]["content"]
    # continue adds to the same line
    cont = stream(app, f"/api/events/{ev['id']}/continue")[-1][1]
    assert cont["content"].endswith("And another thing.")


def test_feelings_are_tracked_and_fed_back(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara, ben]}).json()["id"]
    say(app, sc, "Ben lied to you, Mara.")
    turn(app, sc, mara)
    for _ in range(50):
        story = app.get(f"/api/stories/{sid}").json()
        if story["feelings"].get(str(mara)):
            break
        time.sleep(0.05)
    f = story["feelings"][str(mara)]
    assert f["mood"] == "prickly"
    assert f["toward"][str(ben)] == "doesn't trust them"
    assert f["word"] == "Prickly" and f["strength"][str(ben)] == 4
    assert app.get(f"/api/scenes/{sc}").json()["feelings"][str(mara)]["strength"][str(ben)] == 4
    turn(app, sc, mara)
    tail = app.fake.prompts_for("Mara")[-1]["messages"][-1]["content"]
    assert "How Mara feels right now: prickly" in tail and "About Ben Ortiz: feels doesn't trust them; shows polite" in tail


def test_journal_entries_come_to_mind(app):
    sid, mara, ben, cleo = setup_story(app)
    app.post("/api/journal", json={"story_id": sid, "title": "The letter", "keys": "letter, Paris", "text": "Signed by their mother."})
    app.post("/api/journal", json={"character_id": ben, "title": "Debt", "keys": "money", "text": "Ben owes the Duvals."})
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [ben]}).json()["id"]
    say(app, sc, "Who sent the letter?")
    ev = turn(app, sc, ben)[-1][1]
    tail = app.fake.prompts_for("Ben Ortiz")[-1]["messages"][-1]["content"]
    assert "The letter: Signed by their mother." in tail and "Ben owes" not in tail
    assert any(r["kind"] == "journal" for r in ev["recalled"])


def test_short_term_overflow_is_written_to_memory_first(app):
    sid, mara, ben, cleo = setup_story(app)
    app.put("/api/settings", json={"short_term": "300"})
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    for i in range(8):
        say(app, sc, f"Line number {i} about the orchard and the long winter that came.")
    turn(app, sc, mara)
    p = app.fake.prompts_for("Mara")[-1]
    assert "Line number 0" not in "\n".join(m["content"] for m in p["messages"])
    assert "Mara remembered the argument" in p["messages"][0]["content"]


def test_rewind_star_ideas_and_export(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"title": "Dinner", "characters": [mara]}).json()["id"]
    first = say(app, sc, "Hello.")
    ev = turn(app, sc, mara)[-1][1]
    app.post(f"/api/events/{ev['id']}/star", json={"starred": True, "idea": "Use this in chapter 3"})
    ideas = app.get("/api/ideas").json()
    assert ideas[0]["idea"] == "Use this in chapter 3" and ideas[0]["name"] == "Mara"
    md = app.get(f"/api/stories/{sid}/export").text
    assert "## Dinner" in md and "**Mara:** ⭐ Hello from Mara" in md and "> Use this in chapter 3" in md
    say(app, sc, "Second.")
    app.post(f"/api/events/{first['id']}/rewind")
    assert [e["kind"] for e in app.get(f"/api/scenes/{sc}").json()["events"]] == ["enter"]


def test_end_scene_writes_everyones_memory(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"title": "Dinner", "characters": [mara, ben]}).json()["id"]
    say(app, sc, "Fine.")
    app.post(f"/api/scenes/{sc}/end")
    for cid in (mara, ben):
        mems = app.get(f"/api/characters/{cid}").json()["stories"][0]["memories"]
        assert mems and mems[0]["scene_id"] == sc
    assert app.get(f"/api/characters/{cleo}").json()["stories"][0]["memories"] == []


def test_splitter_handles_pieces_and_no_inner():
    s = engine.Splitter("Mara")
    out = []
    for piece in ["<in", "ner>Hu", "rt.</in", "ner>\n\nMa", "ra: No", "."]:
        out += s.feed(piece)
    out += s.end()
    assert s.inner == "Hurt." and s.text == "No."
    s = engine.Splitter("Mara")
    for piece in ["Fine", ", whatever."]:
        s.feed(piece)
    s.end()
    assert s.inner == "" and s.text == "Fine, whatever."
    s = engine.Splitter("Mara")
    s.feed("<inner>never closed")
    assert ("reset", "never closed") in s.end() and s.text == "never closed"


def test_models_listed_and_errors_said_plainly(app):
    assert [m["id"] for m in app.get(f"/api/connections/{app.conn}/models").json()] == ["fake-large", "fake-small"]
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    out = turn(app, sc, mara, model="999/nothing")
    assert out[-1][0] == "error" and out[-1][1]["code"] == "setup"
