"""Scene aims, what they show, Draft that keeps her words, memory that tidies itself, journal entries
from her pages and from lines, and fair turns with a reason."""
import json
import re

import httpx

from bamah import db, engine, models
from .conftest import FakeModel
from .test_scenes import say, setup_story, turn


def swap(app, monkeypatch, fake):
    monkeypatch.setattr(models, "_transport", httpx.MockTransport(fake))
    app.fake = fake


def scene(app, sid, *who, **kw):
    return app.post(f"/api/stories/{sid}/scenes", json={"title": "Dinner", "setting": "The kitchen", "characters": list(who), **kw}).json()["id"]


def test_a_scene_aim_goes_to_everyone_there(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = scene(app, sid, mara, ben, aim="Ben admits he read the letter.")
    assert app.get(f"/api/scenes/{sc}").json()["aim"] == "Ben admits he read the letter."
    say(app, sc, "So.")
    turn(app, sc, mara)
    system = app.fake.prompts_for("Mara")[-1]["messages"][0]["content"]
    assert "Ben admits he read the letter." in system and "Never say it outright" in system
    app.patch(f"/api/scenes/{sc}", json={"aim": ""})
    turn(app, sc, ben)
    assert "Where the writer wants this scene to go" not in app.fake.prompts_for("Ben Ortiz")[-1]["messages"][0]["content"]


def test_what_they_show_sits_next_to_what_they_feel(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = scene(app, sid, mara, ben)
    say(app, sc, "Ben, the letter.")
    turn(app, sc, mara)
    for _ in range(50):
        f = app.get(f"/api/stories/{sid}").json()["feelings"].get(str(mara))
        if f:
            break
        import time; time.sleep(0.05)
    assert f["toward"][str(ben)] == "doesn't trust them" and f["shows"][str(ben)] == "polite"
    turn(app, sc, mara)
    tail = app.fake.prompts_for("Mara")[-1]["messages"][-1]["content"]
    assert "About Ben Ortiz: feels doesn't trust them; shows polite" in tail and "acts on what they show" in tail


def test_draft_keeps_her_words_and_fills_the_rest(app):
    sid, mara, ben, cleo = setup_story(app)
    app.patch(f"/api/characters/{mara}", json={"voice": "Short. Never says sorry.", "sore_spot": "Her mother's restaurant."})
    out = app.post(f"/api/characters/{mara}/draft", json={"words": "proud"}).json()
    assert "personality" not in out and "voice" not in out and "sore_spot" not in out     # hers stay as they are
    assert out["pronouns"] == "she/her" and out["appearance"] == "Red hair."
    ask = app.fake.requests[-1]["messages"][-1]["content"]
    assert "Who they are: Proud. Never apologizes first." in ask and "How they talk: Short. Never says sorry." in ask
    assert "Write these keys only: pronouns, appearance, inner_life, key_memories" in ask
    # no words needed when there's something to build on; replace starts over
    assert app.post(f"/api/characters/{mara}/draft", json={}).status_code == 200
    assert "personality" in app.post(f"/api/characters/{mara}/draft", json={"replace": True}).json()
    # the sore spot goes to the character
    sc = scene(app, sid, mara)
    say(app, sc, "How's the restaurant?")
    turn(app, sc, mara)
    assert "## Mara's sore spot\nHer mother's restaurant." in app.fake.prompts_for("Mara")[-1]["messages"][0]["content"]


class Keeper(FakeModel):
    """A memory-keeper that notices Mara has moved, and says one thing twice."""

    def __call__(self, request):
        if request.url.path.endswith("/chat/completions"):
            body = json.loads(request.content)
            system, last = body["messages"][0]["content"], body["messages"][-1]["content"]
            if system.startswith("You keep the memory of Mara"):
                self.requests.append(body)
                m = re.search(r"\[m(\d+)\] Mara lives in Lyon", last)
                lines = ["- Mara remembered the argument about Paris."]
                if m:
                    lines = [f"- Mara lives in Paris now (replaces m{m.group(1)})", "- Mara remembered the argument about Paris!"] + lines
                sse = f"data: {json.dumps({'choices': [{'delta': {'content': chr(10).join(lines)}}]})}\n\ndata: [DONE]\n\n"
                return httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})
        return super().__call__(request)


def test_memory_replaces_changed_facts_skips_repeats_and_follows_its_lines(app, monkeypatch):
    swap(app, monkeypatch, Keeper())
    sid, mara, ben, cleo = setup_story(app)
    app.put("/api/settings", json={"feelings": "0"})
    old = app.post("/api/memories", json={"character_id": mara, "story_id": sid, "text": "Mara lives in Lyon."}).json()["id"]
    sc = scene(app, sid, mara, ben)
    first = say(app, sc, "Where do you live now, Mara?")
    turn(app, sc, mara)
    app.post(f"/api/scenes/{sc}/end")
    mems = {m["text"]: m for m in app.get(f"/api/characters/{mara}").json()["stories"][0]["memories"]}
    new = mems["Mara lives in Paris now"]
    assert mems["Mara lives in Lyon."]["replaced_by"] == new["id"]
    assert [t for t in mems if "argument about Paris" in t] == ["Mara remembered the argument about Paris!"]   # once
    assert new["from_seq"] == 1 and new["to_seq"] >= 2
    # what the keeper was shown: what she already remembers, with ids
    shown = next(r for r in reversed(app.fake.requests) if r["messages"][0]["content"].startswith("You keep the memory of Mara"))
    assert f"[m{old}] Mara lives in Lyon." in shown["messages"][-1]["content"]
    # a replaced memory doesn't come back to mind
    with db.connect() as d:
        story = db.row(d.execute("select * from story where id = ?", (sid,)).fetchone())
        ch = engine.character(d, mara)
        assert old not in [m["id"] for m in engine.recall(d, story, ch, "Mara lives Lyon Paris", set(), 9)]
    # taking the lines back takes back what was written from them, and the old fact returns
    app.post(f"/api/events/{first['id']}/rewind")
    mems = {m["text"]: m for m in app.get(f"/api/characters/{mara}").json()["stories"][0]["memories"]}
    assert list(mems) == ["Mara lives in Lyon."] and mems["Mara lives in Lyon."]["replaced_by"] is None
    with db.connect() as d:
        assert d.execute("select upto from condensed where scene_id = ? and character_id = ?", (sc, mara)).fetchone()["upto"] == 0


def test_heat_brings_back_what_keeps_coming_up(app):
    sid, mara, ben, cleo = setup_story(app)
    ids = [app.post("/api/memories", json={"character_id": mara, "story_id": sid, "text": t}).json()["id"]
           for t in ("The letter from Paris, unopened.", "The letter from Paris, in the drawer.")]
    pinned = app.post("/api/memories", json={"character_id": mara, "story_id": sid, "text": "Her mother's knife.", "pinned": True}).json()["id"]
    with db.connect() as d:
        d.execute("update memory set heat = 0.05 where id = ?", (ids[0],))
        d.execute("update memory set heat = 0.9 where id = ?", (ids[1],))
        story = db.row(d.execute("select * from story where id = ?", (sid,)).fetchone())
        ch = engine.character(d, mara)
        assert [m["id"] for m in engine.recall(d, story, ch, "letter Paris", set(), 2)] == [ids[1], ids[0]]
        engine.warm(d, [ids[0]])
        engine.cool(d, sid, mara)
        heat = {r["id"]: (r["heat"], r["recalls"]) for r in d.execute("select id, heat, recalls from memory")}
    assert abs(heat[ids[0]][0] - 0.25 * (0.9 + 0.08 / 5)) < 1e-9 and heat[ids[0]][1] == 1
    assert abs(heat[ids[1]][0] - 0.9 * 0.9) < 1e-9
    assert heat[pinned][0] == 0.6          # pinned ones don't fade


def test_journal_entries_from_her_pages(app):
    sid, mara, ben, cleo = setup_story(app)
    pages = b"Mara Ortiz runs the kitchen.\n\nBen Ortiz drives a van.\n\nMara Ortis hates cinnamon."
    out = app.post("/api/journal/split", files={"file": ("notes.txt", pages, "text/plain")}, data={"story_id": str(sid)}).json()
    assert [e["title"] for e in out["entries"]] == ["Mara Ortiz", "Ben Ortiz", "Mara Ortis"]
    assert out["entries"][0]["keys"] == "Mara"
    assert out["issues"] == [{"kind": "spelling", "entries": [0, 2], "note": "Ortiz or Ortis?"}]     # the bogus one is dropped
    assert app.get(f"/api/stories/{sid}").json()["journal"] == []          # nothing saved until she adds them
    assert app.post("/api/journal/batch", json={"story_id": sid, "entries": out["entries"][:2]}).json()["added"] == 2
    assert len(app.get(f"/api/stories/{sid}").json()["journal"]) == 2
    # the shared journal takes a file too
    assert app.post("/api/import", files={"file": ("world.txt", b"It always rains.", "text/plain")},
                    data={"target": "shared", "target_id": "0"}).json()["words"] == 3


def test_a_journal_entry_from_picked_lines(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = scene(app, sid, mara, ben)
    a = say(app, sc, "Ben hid the letter.")
    b = say(app, sc, "Nice weather.")
    out = app.post(f"/api/scenes/{sc}/journal-entry", json={"event_ids": [a["id"]]}).json()
    assert out["entry"] == {"title": "The letter", "keys": "letter, Paris", "text": "Ben hid a letter from Paris."}
    assert "[Narrator] Ben hid the letter." in app.fake.requests[-1]["messages"][-1]["content"]
    assert app.post(f"/api/scenes/{sc}/journal-entry", json={"event_ids": [b["id"]]}).json() == {"nothing": True}


class Picker(FakeModel):
    def __call__(self, request):
        if request.url.path.endswith("/chat/completions"):
            body = json.loads(request.content)
            if body["messages"][0]["content"].startswith("You run the turn order"):
                self.requests.append(body)
                text = "Cleo - quiet for a while\nBen Ortiz — Mara asked him straight out."
                sse = f"data: {json.dumps({'choices': [{'delta': {'content': text}}]})}\n\ndata: [DONE]\n\n"
                return httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})
        return super().__call__(request)


def test_fair_turns_and_why_they_spoke(app, monkeypatch):
    swap(app, monkeypatch, Picker())
    sid, mara, ben, cleo = setup_story(app)
    sc = scene(app, sid, mara, ben, cleo)
    say(app, sc, "Well?")
    turn(app, sc, mara)
    say(app, sc, "And?")
    assert app.post(f"/api/scenes/{sc}/next", json={}).json()["speakers"] == [cleo, ben]
    ask = app.fake.requests[-1]["messages"][-1]["content"]
    assert "Mara (100% of the lines so far, 1 lines since they last spoke)" in ask
    assert "Cleo (0% of the lines so far, hasn't spoken yet)" in ask
    assert turn(app, sc, cleo)[-1][1]["reason"] == "Quiet for a while"
    assert turn(app, sc, ben)[-1][1]["reason"] == "Mara asked him straight out"
    # a name in her line says why on its own
    say(app, sc, "Mara?")
    app.post(f"/api/scenes/{sc}/next", json={})
    assert turn(app, sc, mara)[-1][1]["reason"] == "Named in your line"
    # stats
    evs = engine.events(db.connect(), sc)
    with db.connect() as d:
        here = engine.present(d, sc)
    stats = engine.turn_stats(evs, here)
    assert stats[mara] == (50, 0) and stats[cleo][1] == 3
