from bamah import engine

from .test_scenes import say, setup_story, turn


def entry(i, keys, **kw):
    return {"id": i, "title": f"e{i}", "keys": keys, "text": "x", **kw}


def test_keyphrases_match_whole_words():
    low = engine._plain("Ben sat on the bench by the bridges, in Odile’s café.")
    assert engine.mentions("Ben", low)
    assert engine.mentions("bridge", low)                   # a plural still counts
    assert engine.mentions("Odile's café", low)             # either apostrophe
    assert not engine.mentions("Benny", low)
    assert not engine.mentions("bench press", low)
    assert not engine.mentions("bri", low)
    assert not engine.mentions("Ben", engine._plain("The bench was cold."))
    assert engine.mentions("東京", engine._plain("彼は東京へ行った"))  # scripts without spaces match anywhere


def test_off_entries_never_come_and_pinned_come_first():
    entries = [entry(i, "rain") for i in range(1, 11)]
    entries[3]["enabled"] = 0
    entries[9]["pinned"] = 1
    hits, over = engine.journal_pick(entries, "It looked like rain.")
    assert [j["id"] for j in hits] == [10, 1, 2, 3, 5, 6, 7, 8]
    assert [j["id"] for j in over] == [9]
    always, _ = engine.journal_pick([entry(1, ""), entry(2, "", enabled=0)], "anything")
    assert [j["id"] for j in always] == [1]


def test_switch_pin_and_try_a_line(app):
    sid, mara, ben, cleo = setup_story(app)
    bench = app.post("/api/journal", json={"story_id": sid, "title": "The bench", "keys": "bench", "text": "Painted green."}).json()["id"]
    debt = app.post("/api/journal", json={"story_id": sid, "title": "Ben's debt", "keys": "Ben", "text": "Owes the Duvals."}).json()["id"]
    app.post("/api/journal", json={"title": "The town", "keys": "town", "text": "Ensenada."})
    other = app.post("/api/stories", json={"title": "Winter Term"}).json()["id"]
    app.post("/api/journal", json={"story_id": other, "title": "Elsewhere", "keys": "bench", "text": "Not this story."})

    tried = app.post("/api/journal/try", json={"story_id": sid, "text": "He sat on the bench in town."}).json()
    assert [x["title"] for x in tried["hits"]] == ["The bench", "The town"] and tried["over"] == []

    app.patch(f"/api/journal/{bench}", json={"enabled": 0})
    app.patch(f"/api/journal/{debt}", json={"pinned": 1})
    tried = app.post("/api/journal/try", json={"story_id": sid, "text": "Ben sat on the bench."}).json()
    assert [x["title"] for x in tried["hits"]] == ["Ben's debt"]
    row = next(j for j in app.get(f"/api/stories/{sid}").json()["journal"] if j["id"] == bench)
    assert row["enabled"] == 0 and row["pinned"] == 0

    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara]}).json()["id"]
    say(app, sc, "Meet me at the bench.")
    turn(app, sc, mara)
    tail = app.fake.prompts_for("Mara")[-1]["messages"][-1]["content"]
    assert "Painted green" not in tail
