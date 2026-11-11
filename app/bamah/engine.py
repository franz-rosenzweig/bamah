"""How a scene runs: who speaks, what each character knows, and what they remember and feel afterwards.

Every character sees only what they were there for (unless the story is set to "everyone knows
everything"). Every line in a scene records who was in the room, so when a character moves to
another scene, their memory goes with them, and nobody knows what they didn't see.

Memory comes in layers, the way people have it:
- the scene so far, word for word, as far back as the short-term size allows;
- memories: short notes written from the character's own point of view whenever a stretch of a
  scene falls out of short-term (and whenever they leave a scene, or it ends);
- what they have come to know in this story: running notes on relationships, facts and open threads;
- how they feel right now, about the moment and about each of the others;
- journal entries, which come to mind when one of their keyphrases comes up.
"""

import asyncio
import json
import logging
import re

from . import db, models
from .models import ModelError

log = logging.getLogger("bamah.engine")

STYLE = {
    "roleplay": "Write it the way roleplay is written: what {name} says, with actions and small physical details in *asterisks*.",
    "narrative": "Write it as novel prose, past tense: what {name} says and does, and only what can be seen and heard.",
    "dialogue": "Keep it to what {name} says out loud, with at most a few words of action in *asterisks*.",
}
PERSON = {
    "first": "Write as {name}, in the first person, actions included (*I set the cup down.*).",
    "third": "Write about {name} in the third person{pron}.",
}
LENGTH = {
    "short": "Keep it short, the way people really talk: usually a line or two.",
    "medium": "Take as long as the moment needs: usually a short paragraph, longer only when {name} would really go on.",
    "long": "Give the moment room: a few paragraphs when there's something to say or do.",
}

INTRO = """You are playing {name} in a story a novelist is developing. She uses these scenes to find out how her characters really behave, so the one thing that matters is that {name} acts like {name}: their own wants, fears, wounds, blind spots, pride and sense of humor, even when that's inconvenient, rude, petty or cruel. Don't soften them, don't make them wiser or kinder than they are, and don't tie things up neatly. Let them surprise her the way real people do, without ever stepping out of who they are.

Read the emotional temperature of every moment the way {name} would: what was said, what was meant, what was left out, who is hurt, who is showing off, who is hiding something. {name} reacts to what they feel and what they notice, which is not always what's polite or what's said out loud. Feelings carry over: a slight from earlier is still there, trust that was broken stays broken until something mends it.

Start every turn with {name}'s inner state inside <inner></inner>: a sentence or two on what they feel right now and why, what they want from this moment, and what they're keeping to themselves. Only the writer reads it; the others in the scene never do. Then write the turn itself.

Write only {name}'s turn: what they say and do. Never speak or act for anyone else, never decide what the others do next, and never describe what they think or feel. Don't put "{name}:" in front. {person} {style} {length}"""

WITNESSED = "{name} only knows what they've seen, heard or been told. If they weren't there, they don't know it, even when you do."

MEMORY_SYSTEM = """You keep the memory of {name}, a character in a story. Below is part of a scene as {name} experienced it. Write what {name} will remember of it: what happened, what was said that mattered, how they felt about it and about the others, and anything they learned about someone. Write from {name}'s point of view but in the third person, past tense, as two to eight short notes, each on its own line starting with "- ". Only what {name} saw, heard or was told. Be concrete: names, places, promises, insults, secrets, who took whose side.

Some of what {name} already remembers comes first, each with an id like [m12]. Don't write any of it again. If a new note changes something that was true until now (where someone lives, what they plan, who they're with, what they believe, how things stand between two people), end that note with "(replaces m12)", using the old one's id. Never replace a memory of something that happened: what happened stays. Return only the notes."""

LEARNED_SYSTEM = """You keep {name}'s running notes for one story. Update the notes with the new memories below. Keep exactly these three sections, each a few short lines:

Relationships and growth
Important facts
Ongoing threads

Under relationships, say how {name} stands with each person who matters to them, and how that has been changing. Keep everything that still holds, change what the new memories changed, and drop what no longer matters. Stay under 1,500 characters. Return only the notes."""

FEELING_SYSTEM = """You keep track of how the characters in a story feel, and how much of it they let show. Read the latest moment and say how {name} feels now. Answer with JSON only, in this shape:
{{"word": "one word for how {name} feels right now", "mood": "how {name} feels right now, in a few words", "toward": {{"<name of someone in the story>": {{"how": "how {name} really feels about them now, in a few words", "shows": "what {name} lets them see, in a few words", "strength": <1 to 5, how strongly {name} feels it>}}}}}}
"shows" is the face {name} puts on for that person, like "polite, a little too cheerful" or "nothing at all". It can match what they feel, when {name} is open with them, or be far from it, when {name} is hiding it; judge from how {name} is and from what they actually said and did. Include everyone {name} has feelings about. Keep what still holds from before, and change only what this moment changed."""

PICK_SYSTEM = """You run the turn order in a group scene of a story. From the last lines, decide who in the room would naturally speak or react next, in order, at most {most}. Each person comes with their share of the lines so far and how long it's been since they last spoke. Don't leave anyone silent for long unless the scene calls for it (someone sulking, listening, or out of it), and don't let one person take over unless the moment is theirs.
Answer with one person per line: their name, then " - ", then a few words on why them, like "Ben - Mara asked him straight out" or "Cleo - quiet for 6 lines". Reply NOBODY if nobody would."""

STOP = set("""about above after again against also among another because been before being below between both
cannot could does doing down during each from further have having here hers herself himself into itself just more
most never only other ours ourselves over same should some such than that their theirs them themselves then there
these they this those through under until very were what when where which while whom with would your yours yourself
yourselves will shall said says like know want yeah okay well even still really maybe something nothing anything
everything someone anyone thing things going come came make made take took give gave tell told look looked""".split())

_locks: dict[tuple, asyncio.Lock] = {}
_reasons: dict[tuple, str] = {}          # (scene, character): why the turn order picked them, for their next line


def _lock(*key) -> asyncio.Lock:
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]


# --- Reading the scene ------------------------------------------------------------------------

def story_of(d, scene_id: int) -> tuple[dict, dict]:
    scene = db.row(d.execute("select * from scene where id = ?", (scene_id,)).fetchone())
    if not scene:
        raise KeyError("scene")
    story = db.row(d.execute("select * from story where id = ?", (scene["story_id"],)).fetchone())
    return story, scene


def character(d, cid: int) -> dict:
    ch = db.row(d.execute("select * from character where id = ?", (cid,)).fetchone())
    if not ch:
        raise KeyError("character")
    return ch


def present(d, scene_id: int) -> list[dict]:
    return db.rows(d.execute(
        "select c.* from presence p join character c on c.id = p.character_id "
        "where p.scene_id = ? and p.left_seq is null order by p.id", (scene_id,)))


def cast(d, story_id: int) -> list[dict]:
    return db.rows(d.execute(
        "select c.* from cast_member m join character c on c.id = m.character_id where m.story_id = ? order by c.name",
        (story_id,)))


def events(d, scene_id: int, before: int | None = None) -> list[dict]:
    q = "select * from event where scene_id = ?" + (" and seq < ?" if before is not None else "") + " order by seq"
    return db.rows(d.execute(q, (scene_id, before) if before is not None else (scene_id,)))


def seen_by(evs: list[dict], cid: int, story: dict) -> list[dict]:
    if story["memory"] == "shared":
        return evs
    return [e for e in evs if cid in (e["witnesses"] or [])]


def next_seq(d, scene_id: int) -> int:
    return (d.execute("select max(seq) from event where scene_id = ?", (scene_id,)).fetchone()[0] or 0) + 1


def names(d) -> dict[int, str]:
    return {r["id"]: r["name"] for r in d.execute("select id, name from character")}


def line(e: dict, who: dict[int, str]) -> str:
    """One event as the others see it (no inner thoughts)."""
    if e["kind"] == "you":
        sp = (e["speaker"] or "").strip()
        return f"[Narrator] {e['content']}" if not sp or sp.lower() == "narrator" else f"{sp}: {e['content']}"
    if e["kind"] == "enter":
        return f"[{who.get(e['character_id'], 'Someone')} comes in.]"
    if e["kind"] == "leave":
        return f"[{who.get(e['character_id'], 'Someone')} leaves.]"
    if e["kind"] == "doc":
        return f"[A document everyone here has read, “{e['speaker'] or 'Untitled'}”:]\n{e['content']}"
    return f"{who.get(e['character_id'], 'Someone')}: {e['content']}"


# --- Model choice -----------------------------------------------------------------------------

def model_for(d, story: dict, ch: dict | None) -> str | None:
    return (ch or {}).get("model") or story.get("model") or db.setting(d, "default_model")


def helper_model(d, story: dict | None = None) -> str | None:
    return db.setting(d, "helper_model") or (story or {}).get("model") or db.setting(d, "default_model")


# --- Building a character's prompt ------------------------------------------------------------

def _words(text: str) -> list[str]:
    seen, out = set(), []
    for w in re.findall(r"[^\W\d_]{4,}", text.lower()):
        if w not in STOP and w not in seen:
            seen.add(w)
            out.append(w)
    return out[:16]


def base_memories(d, story: dict, ch: dict, budget: int = 6000) -> list[dict]:
    """Pinned memories, then the newest, within the budget. In a shared story, others' memories of
    scenes this character wasn't in come along too."""
    mems = db.rows(d.execute(
        "select m.*, s.title as scene_title, s.seq as scene_seq from memory m left join scene s on s.id = m.scene_id "
        "where m.story_id = ? and m.character_id = ? and m.replaced_by is null order by m.pinned desc, m.id desc", (story["id"], ch["id"])))
    if story["memory"] == "shared":
        mine = {m["scene_id"] for m in mems}
        others = db.rows(d.execute(
            "select m.*, s.title as scene_title, s.seq as scene_seq from memory m left join scene s on s.id = m.scene_id "
            "where m.story_id = ? and m.character_id != ? and m.replaced_by is null order by m.id desc", (story["id"], ch["id"])))
        firsts: dict = {}
        for m in others:
            if m["scene_id"] not in mine:
                firsts.setdefault(m["scene_id"], m["character_id"])
                if firsts[m["scene_id"]] == m["character_id"]:
                    mems.append(m)
    out, used = [], 0
    for m in mems:
        if not m["pinned"] and used + len(m["text"]) > budget:
            continue
        out.append(m)
        used += len(m["text"])
    out.sort(key=lambda m: (m["scene_seq"] or 0, m["id"]))
    return out


COLD = 0.15         # below this a memory has faded: it comes back less readily, and shows dimmed


def recall(d, story: dict, ch: dict, text: str, skip: set, most: int) -> list[dict]:
    """The memories that match what's happening, best first. The full-text match is weighed with each
    memory's heat, so what keeps coming back comes back more readily, and faded ones less."""
    words = _words(text)
    if not words or most <= 0:
        return []
    q = " OR ".join(f'"{w}"' for w in words)
    who = "" if story["memory"] == "shared" else " and m.character_id = :cid"
    try:
        found = db.rows(d.execute(
            "select m.*, s.title as scene_title, bm25(memory_fts) as score from memory_fts f join memory m on m.id = f.rowid "
            "left join scene s on s.id = m.scene_id where memory_fts match :q and m.story_id = :sid and m.replaced_by is null" + who +
            " order by bm25(memory_fts) limit :n", {"q": q, "sid": story["id"], "cid": ch["id"], "n": 3 * most + len(skip)}))
    except Exception:          # an FTS query it can't parse: no recall this turn
        return []

    def weight(m):
        heat = 1.0 if m["pinned"] else (m.get("heat") if m.get("heat") is not None else 0.6)
        w = m["score"] * (0.6 + 0.8 * heat)          # bm25 is negative: more negative is a better match
        return w * 0.5 if heat < COLD else w
    found = [m for m in found if m["id"] not in skip]
    found.sort(key=weight)
    return found[:most]


def warm(d, ids: list[int]):
    """These came back to mind: they grow warmer, and fade more slowly from now on."""
    if ids:
        d.execute(f"update memory set heat = min(1.0, coalesce(heat, 0.6) + 0.2), recalls = coalesce(recalls, 0) + 1, "
                  f"last_recalled = datetime('now') where id in ({','.join('?' * len(ids))})", ids)


def cool(d, story_id: int, cid: int):
    """After each memory-writing pass, everything not pinned fades a little; what has come back often, less."""
    d.execute("update memory set heat = coalesce(heat, 0.6) * (0.9 + 0.08 * min(coalesce(recalls, 0), 5) / 5.0) "
              "where story_id = ? and character_id = ? and pinned = 0 and replaced_by is null", (story_id, cid))


def _norm(text: str) -> str:
    return " ".join(re.findall(r"[\w']+", text.lower()))


def same_memory(a: str, b: str) -> bool:
    """The same note twice: identical once normalized, or most of the words the same."""
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return True
    wa, wb = {w for w in na.split() if len(w) > 2}, {w for w in nb.split() if len(w) > 2}
    return bool(wa and wb) and len(wa & wb) / len(wa | wb) >= 0.8


UNSPACED = re.compile(r"[぀-ヿ㐀-鿿가-힯]")   # scripts written without spaces


def _plain(text: str) -> str:
    return text.lower().replace("’", "'")


def mentions(key: str, low: str) -> bool:
    """Whether a keyphrase comes up in the text, as a whole word or phrase (or its plural):
    "Ben" comes up in "Ben's coat" but not in "bench". low is the text through _plain()."""
    key = _plain(key)
    if UNSPACED.search(key):
        return key in low
    return re.search(r"(?<!\w)" + re.escape(key) + r"(?:e?s)?(?!\w)", low) is not None


def journal_pick(entries: list[dict], text: str, most: int = 8) -> tuple[list[dict], list[dict]]:
    """The entries that come to mind for this text, pinned ones first, and the ones past the limit.
    An entry that's switched off never comes to mind; one with no keyphrases always does."""
    low = _plain(text)
    hits = []
    for j in entries:
        if j.get("enabled") == 0:
            continue
        keys = [k.strip() for k in (j["keys"] or "").split(",") if k.strip()]
        if not keys or any(mentions(k, low) for k in keys):
            hits.append(j)
    hits.sort(key=lambda j: (-(j.get("pinned") or 0), j["id"]))
    return hits[:most], hits[most:]


def journal_hits(d, story: dict, ch: dict, text: str, most: int = 8) -> list[dict]:
    entries = db.rows(d.execute(
        "select * from journal where (story_id is null or story_id = ?) and (character_id is null or character_id = ?) "
        "order by id", (story["id"], ch["id"])))
    return journal_pick(entries, text, most)[0]


def feeling_now(d, story_id: int, cid: int) -> dict | None:
    return db.row(d.execute("select * from feeling where story_id = ? and character_id = ? order by id desc limit 1",
                            (story_id, cid)).fetchone())


def personas_for(d, story: dict, ch: dict | None = None) -> list[dict]:
    """The people the writer plays in this story, plus the one this character is tied to."""
    ids = list(story.get("personas") or [])
    if ch and ch.get("persona_id") and ch["persona_id"] not in ids:
        ids.append(ch["persona_id"])
    if not ids:
        return []
    rows = db.rows(d.execute(f"select * from persona where id in ({','.join('?' * len(ids))})", ids))
    return sorted(rows, key=lambda r: ids.index(r["id"]))


def system_prompt(d, story: dict, scene: dict, ch: dict, mems: list[dict]) -> str:
    name = ch["name"]
    pron = (ch.get("pronouns") or "").strip()
    person = ch.get("person") or story.get("person") or "first"
    parts = [INTRO.format(name=name, style=STYLE.get(ch.get("style") or story["style"], STYLE["roleplay"]).format(name=name),
                          person=PERSON.get(person, PERSON["first"]).format(name=name, pron=f" ({pron})" if pron else ""),
                          length=LENGTH.get(story["length"], LENGTH["medium"]).format(name=name))]
    if story["memory"] != "shared":
        parts[0] += "\n\n" + WITNESSED.format(name=name)
    parts.append(f"# {name}{f' ({pron})' if pron else ''}\n{ch['personality'].strip() or '(The writer has only given a name so far.)'}")
    if (ch.get("appearance") or "").strip():
        parts.append(f"## What {name} looks like\n{ch['appearance'].strip()}")
    if ch["inner_life"].strip():
        parts.append(f"## {name}'s inner life\n{ch['inner_life'].strip()}")
    if (ch.get("sore_spot") or "").strip():
        parts.append(f"## {name}'s sore spot\n{ch['sore_spot'].strip()}\nWhen someone presses on it, {name} reacts, in their own way: "
                     f"they might dodge it, go cold, flare up or change the subject, but it never slides past them.")
    if ch["key_memories"].strip():
        parts.append(f"## Things {name} always remembers\n{ch['key_memories'].strip()}")
    if ch["voice"].strip():
        parts.append(f"## How {name} talks\n{ch['voice'].strip()}")
    examples = d.execute("select text from example where character_id = ? order by id desc limit 8", (ch["id"],)).fetchall()
    if examples:
        parts.append(f"## Lines of {name}'s that sounded exactly right\n" + "\n".join(f"- {r['text']}" for r in reversed(examples)))
    fixes = d.execute("select text from correction where character_id = ? order by id", (ch["id"],)).fetchall()
    if fixes:
        parts.append(f"## The writer's corrections about {name} (these always win)\n" + "\n".join(f"- {r['text']}" for r in fixes))
    if ch["directive"].strip():
        parts.append(f"## Always\n{ch['directive'].strip()}")
    parts.append(f"# The story: {story['title']}\n{story['premise'].strip()}".rstrip())
    if story["directive"].strip():
        parts.append(f"## How this story is written\n{story['directive'].strip()}")
    people = personas_for(d, story, ch)
    if people:
        lines = []
        for p in people:
            label = p["name"] + (f" ({p['pronouns']})" if p.get("pronouns") else "")
            lines.append(f"- {label}: {p.get('about', '')}".rstrip(": "))
        parts.append("## People the writer plays\n" + "\n".join(lines))
        tied = next((p for p in people if p["id"] == ch.get("persona_id")), None)
        if tied:
            parts.append(f"## Who {name} is usually with\nThe writer usually plays {tied['name']} opposite {name}.")
    learned = d.execute("select text from learned where story_id = ? and character_id = ?", (story["id"], ch["id"])).fetchone()
    if learned and learned["text"].strip():
        parts.append(f"# What {name} has come to know in this story\n{learned['text'].strip()}")
    if mems:
        lines = []
        for m in mems:
            where = f"({m['scene_title']}) " if m.get("scene_title") else ""
            lines.append(f"- {where}{m['text']}")
        parts.append(f"# What {name} remembers\n" + "\n".join(lines))
    parts.append(f"# This scene: {scene['title'] or 'Untitled'}\n{scene['setting'].strip()}".rstrip())
    if (scene.get("aim") or "").strip():
        parts.append(f"## Where the writer wants this scene to go (only she knows this)\n{scene['aim'].strip()}\n"
                     f"Let {name} push toward it in {name}'s own way, at {name}'s own pace, the way {name} would get there. "
                     f"Never say it outright, never mention that there's a plan, and never force it.")
    return "\n\n".join(parts)


def transcript(evs: list[dict], ch: dict, who: dict[int, str], budget: int) -> tuple[list[dict], int | None]:
    """The scene as messages, newest kept first within the budget. Returns them and the first seq kept."""
    kept, used = [], 0
    for e in reversed(evs):
        text = e["content"] if (e["kind"] == "character" and e["character_id"] == ch["id"]) else line(e, who)
        if used + len(text) > budget and kept:
            break
        kept.append((e, text))
        used += len(text)
    kept.reverse()
    msgs: list[dict] = []
    for e, text in kept:
        role = "assistant" if (e["kind"] == "character" and e["character_id"] == ch["id"]) else "user"
        if msgs and msgs[-1]["role"] == role:
            msgs[-1]["content"] += "\n\n" + text
        else:
            msgs.append({"role": role, "content": text})
    return msgs, (kept[0][0]["seq"] if kept else None)


def _short(text: str | None, most: int = 160) -> str:
    t = " ".join((text or "").split())
    if len(t) <= most:
        return t
    cut = t[:most]
    end = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[:end + 1] if end > 40 else cut.rsplit(" ", 1)[0] + "…").strip()


def repeated(lines: list[str], most: int = 6) -> list[str]:
    """Phrases a character keeps reaching for: word runs that turn up in several of their recent lines."""
    seen: dict[str, int] = {}
    openers: dict[str, int] = {}
    for text in lines:
        words = re.findall(r"[\w']+", text.lower())
        found = set()
        for n in (5, 4, 3):
            for i in range(len(words) - n + 1):
                gram = words[i:i + n]
                if sum(w not in STOP and len(w) > 2 for w in gram) < 2:
                    continue
                found.add(" ".join(gram))
        for g in found:
            seen[g] = seen.get(g, 0) + 1
        if len(words) >= 3:
            o = " ".join(words[:3])
            openers[o] = openers.get(o, 0) + 1
    hits = sorted((g for g, c in seen.items() if c >= 2), key=lambda g: (-seen[g], -len(g)))
    out: list[str] = []
    for g in hits + [o for o, c in openers.items() if c >= 3]:
        if not any(g in o or o in g for o in out):
            out.append(g)
        if len(out) >= most:
            break
    return out


def nudge(d, story: dict, scene: dict, ch: dict, here: list[dict], recalled: list[dict], notes: list[dict],
          note: str | None, mode: str, speakers=(), repeats=()) -> str:
    name = ch["name"]
    who = names(d)
    lines = []
    others = []
    for c in here:
        if c["id"] == ch["id"]:
            continue
        bits = [b for b in ((c.get("pronouns") or "").strip(), _short(c.get("appearance"))) if b]
        others.append(c["name"] + (f" ({'; '.join(bits)})" if bits else ""))
    others += [s for s in speakers if s]
    lines.append("[Here with " + name + ": " + (", ".join(others) if others else "nobody else") + ".]")
    f = feeling_now(d, story["id"], ch["id"])
    if f and (f["mood"] or f["toward"]):
        parts = [f"[How {name} feels right now: {f['mood']}".rstrip(": ")]
        shown = f.get("shows") or {}
        for oid, how in (f["toward"] or {}).items():
            other = who.get(int(oid)) if str(oid).isdigit() else str(oid)
            if other and how:
                face = shown.get(str(oid))
                parts.append(f"About {other}: feels {how}; shows {face}" if face else f"About {other}: {how}")
        lines.append(". ".join(parts) + ".]")
        if any(shown.values()):
            lines.append(f"[{name} acts on what they show. What they feel only leaks out in small ways: a pause, a word too many, "
                         f"a look, a joke that lands wrong, unless something pushes it out into the open.]")
    if recalled:
        lines.append(f"[What comes back to {name} right now:\n" + "\n".join(f"- {m['text']}" for m in recalled) + "]")
    if notes:
        lines.append("[Notes:\n" + "\n".join(f"- {(j['title'] + ': ') if j['title'] else ''}{j['text']}" for j in notes) + "]")
    if note:
        lines.append(f"[The writer's note for this turn: {note}]")
    if repeats and mode != "continue":
        lines.append(f"[{name} has been leaning on these lately; find fresh words this time: "
                     + ", ".join(f"“{r}”" for r in repeats) + ".]")
    if mode == "continue":
        lines.append(f"[Continue {name}'s last turn from exactly where it stops, without repeating any of it. No <inner> this time.]")
    else:
        lines.append(f"[Write {name}'s next turn.]")
    return "\n".join(lines)


async def prompt(scene_id: int, cid: int, *, before: int | None = None, note: str | None = None,
                 mode: str = "new") -> dict:
    """Everything one character's turn needs. before: only the events before this seq (for a redo)."""
    with db.connect() as d:
        story, scene = story_of(d, scene_id)
    await catch_up(story["id"], cid, except_scene=scene_id)
    with db.connect() as d:
        ch = character(d, cid)
        budget = int(db.setting(d, "short_term") or 60000)
        evs = seen_by(events(d, scene_id, before), cid, story)
        if mode == "continue" and before is not None:
            last = db.row(d.execute("select * from event where scene_id = ? and seq = ?", (scene_id, before)).fetchone())
            if last:
                evs.append(last)
        who = names(d)
        msgs, first = transcript(evs, ch, who, budget)
        # Anything that fell out of short-term but isn't in memory yet gets written down first.
        done = d.execute("select upto from condensed where scene_id = ? and character_id = ?", (scene_id, cid)).fetchone()
        missing = first is not None and any(e["seq"] < first and e["seq"] > (done["upto"] if done else 0) for e in evs)
    if missing:
        await condense(scene_id, cid, upto=first - 1)
    with db.connect() as d:
        ch = character(d, cid)
        here = present(d, scene_id)
        mems = base_memories(d, story, ch)
        recent = " ".join(e["content"] for e in evs[-3:] if e["kind"] in ("you", "character"))
        recalled = recall(d, story, ch, recent, {m["id"] for m in mems}, int(db.setting(d, "recall") or 6))
        warm(d, [m["id"] for m in recalled])
        mine = [e for e in evs if e["kind"] == "you"][-1:]
        trigger = " ".join(e["content"] for e in (evs[-3:] + mine)) + " " + scene["setting"]
        notes = journal_hits(d, story, ch, trigger)
        system = system_prompt(d, story, scene, ch, mems)
        speakers = []
        for e in evs:
            sp = (e["speaker"] or "").strip()
            if e["kind"] == "you" and sp and sp.lower() != "narrator" and sp not in speakers:
                speakers.append(sp)
        repeats = []
        if db.setting(d, "repetition") == "1":
            own = [e["content"] for e in evs if e["kind"] == "character" and e["character_id"] == cid][-12:]
            repeats = repeated(own)
        tail = nudge(d, story, scene, ch, here, recalled, notes, note, mode, speakers, repeats)
        if msgs and msgs[-1]["role"] == "user":
            msgs[-1]["content"] += "\n\n" + tail
        else:
            msgs.append({"role": "user", "content": tail})
        if msgs[0]["role"] != "user":
            msgs.insert(0, {"role": "user", "content": "[The scene begins.]"})
        return {"system": system, "messages": msgs, "character": ch, "story": story, "scene": scene, "tail": tail,
                "here": [c["id"] for c in here],
                "recalled": [{"kind": "memory", "id": m["id"], "text": m["text"]} for m in recalled] +
                            [{"kind": "journal", "id": j["id"], "text": (j["title"] + ": " if j["title"] else "") + j["text"]}
                             for j in notes]}


# --- Splitting the inner state from the turn as it streams -----------------------------------

class Splitter:
    """Pulls <inner>…</inner> off the front of a reply, and a stray "Name:" off the turn."""

    def __init__(self, name: str, inner: bool = True):
        self.name, self.buf, self.inner, self.text = name, "", "", ""
        self.mode = "start" if inner else "lead"

    def feed(self, piece: str) -> list[tuple[str, str]]:
        self.buf += piece
        out = []
        while True:
            if self.mode == "start":
                s = self.buf.lstrip()
                if not s:
                    return out
                if s.startswith("<inner>"):
                    self.buf, self.mode = s[7:], "inner"
                    continue
                if len(s) < 7 and "<inner>".startswith(s):
                    return out
                self.buf, self.mode = s, "lead"
                continue
            if self.mode == "inner":
                i = self.buf.find("</inner>")
                if i >= 0:
                    self._inner(self.buf[:i], out)
                    self.buf, self.mode = self.buf[i + 8:], "lead"
                    continue
                if len(self.buf) > 8:
                    self._inner(self.buf[:-8], out)
                    self.buf = self.buf[-8:]
                return out
            if self.mode == "lead":
                s = self.buf.lstrip()
                if not s:
                    self.buf = ""
                    return out
                tag = self.name + ":"
                if len(s) < len(tag) and tag.lower().startswith(s.lower()):
                    self.buf = s
                    return out
                if s.lower().startswith(tag.lower()):
                    s = s[len(tag):].lstrip()
                self.buf, self.mode = s, "text"
                continue
            if self.buf:
                self.text += self.buf
                out.append(("text", self.buf))
                self.buf = ""
            return out

    def _inner(self, s: str, out):
        if s:
            self.inner += s
            out.append(("inner", s))

    def end(self) -> list[tuple[str, str]]:
        out = []
        if self.mode == "inner":          # never closed: it was the turn after all
            text, self.inner = self.inner + self.buf, ""
            self.text += text
            out.append(("reset", text))
        elif self.buf:
            self.text += self.buf
            out.append(("text", self.buf))
        self.buf = ""
        return out


# --- Running a turn ---------------------------------------------------------------------------

async def turn(scene_id: int, cid: int, *, model: str | None = None, redo: int | None = None,
               note: str | None = None, save_note: bool = False, cont: int | None = None):
    """Stream one character's turn as (kind, data) pairs: inner, text, reset, done (the saved event), error.
    redo: an event id to take again. cont: an event id to continue."""
    target = None
    with db.connect() as d:
        if redo or cont:
            target = db.row(d.execute("select * from event where id = ?", (redo or cont,)).fetchone())
            if not target or target["kind"] != "character":
                yield ("error", {"code": "request", "detail": "nothing to redo"})
                return
            cid, scene_id = target["character_id"], target["scene_id"]
        story, scene = story_of(d, scene_id)
        ch = character(d, cid)
        ref = model or model_for(d, story, ch)
        if save_note and note:
            d.execute("insert into correction(character_id, text, event_id) values (?, ?, ?)",
                      (cid, note.strip(), redo))
    mode = "continue" if cont else "new"
    p = await prompt(scene_id, cid, before=target["seq"] if target else None,
                     note=None if save_note else note, mode=mode)
    split = Splitter(ch["name"], inner=mode != "continue")
    try:
        async for piece in _voice(ref, p, scene_id, cid, redo=bool(redo), cont=bool(cont), note=note):
            for kind, data in split.feed(piece):
                yield (kind, data)
        for kind, data in split.end():
            yield (kind, data)
    except ModelError as e:
        log.warning("turn: %s %s", e.code, e.detail)
        yield ("error", {"code": e.code, "detail": e.detail})
        return
    text, inner = split.text.strip(), split.inner.strip()
    if not text:
        yield ("error", {"code": "empty", "detail": ""})
        return
    with db.connect() as d:
        take = {"content": text, "inner": inner, "model": ref}
        if cont:
            ev = db.row(d.execute("select * from event where id = ?", (cont,)).fetchone())
            content = ev["content"].rstrip() + ("\n\n" if text[:1].isupper() else " ") + text
            versions = ev["versions"] or []
            if versions and 0 <= ev["pick"] < len(versions):
                versions[ev["pick"]]["content"] = content
            d.execute("update event set content = ?, versions = ? where id = ?", (content, json.dumps(versions), cont))
            eid = cont
        elif redo:
            ev = db.row(d.execute("select * from event where id = ?", (redo,)).fetchone())
            versions = (ev["versions"] or []) + [take]
            d.execute("update event set content = ?, inner = ?, model = ?, versions = ?, pick = ?, recalled = ?, rating = 0 "
                      "where id = ?", (text, inner, ref, json.dumps(versions), len(versions) - 1,
                                       json.dumps(p["recalled"]), redo))
            d.execute("delete from example where event_id = ?", (redo,))
            eid = redo
        else:
            seq = next_seq(d, scene_id)
            cur = d.execute(
                "insert into event(scene_id, seq, kind, character_id, content, inner, versions, model, witnesses, recalled, reason) "
                "values (?, ?, 'character', ?, ?, ?, ?, ?, ?, ?, ?)",
                (scene_id, seq, cid, text, inner, json.dumps([take]), ref, json.dumps(p["here"]), json.dumps(p["recalled"]),
                 _reasons.pop((scene_id, cid), "")))
            eid = cur.lastrowid
        ev = event_out(d, eid)
    yield ("done", ev)
    if inner and not cont:
        with db.connect() as d:
            on = db.setting(d, "feelings") == "1"
        if on:
            asyncio.create_task(_safe(update_feelings(story["id"], scene_id, cid, eid)))


async def _voice(ref, p, scene_id, cid, *, redo, cont, note):
    """The reply, from a model, or from an outside character service that plays the part itself."""
    s = models.split(ref)
    conn = models.connection(s[0]) if s else None
    play = models.TURNS.get(conn["preset"]) if conn else None
    if play:
        async for piece in play(conn, s[1], p, scene_id=scene_id, cid=cid, redo=redo, cont=cont, note=note):
            yield piece
    else:
        async for piece in models.stream(ref, p["system"], p["messages"], effort="medium"):
            yield piece


def text_model(d, story: dict | None = None, ch: dict | None = None) -> str | None:
    """A model that can write freely (not a service that only plays one character)."""
    for ref in ((ch or {}).get("model"), (story or {}).get("model"), db.setting(d, "default_model"),
                db.setting(d, "helper_model")):
        s = models.split(ref)
        if not s:
            continue
        c = d.execute("select preset from connection where id = ?", (s[0],)).fetchone()
        if c and c["preset"] not in models.TURNS:
            return ref
    return None


async def _safe(coro):
    try:
        await coro
    except Exception:
        log.exception("background")


def event_out(d, eid: int) -> dict:
    e = db.row(d.execute("select * from event where id = ?", (eid,)).fetchone())
    if e and e.get("model"):
        e["model_label"] = models.label(e["model"])
    for v in (e or {}).get("versions") or []:
        v["model_label"] = models.label(v.get("model"))
    return e


# --- Who speaks next --------------------------------------------------------------------------

def mentioned(text: str, here: list[dict]) -> list[int]:
    found = []
    for c in here:
        first = c["name"].split()[0]
        for n in {c["name"], first}:
            m = re.search(r"(?<![\w])@?" + re.escape(n) + r"(?![\w])", text, re.I)
            if m:
                found.append((m.start(), c["id"]))
                break
    return [cid for _, cid in sorted(found)]


async def pick(scene_id: int, *, more: bool = False) -> list[int]:
    """Who answers now. more: she asked them to keep going without saying anything. Each pick's reason
    is kept for the line they write next."""
    order = await _pick(scene_id, more=more)
    for cid, why in order:
        _reasons[(scene_id, cid)] = why
    return [cid for cid, _ in order]


def turn_stats(evs: list[dict], here: list[dict]) -> dict[int, tuple[int, int | None]]:
    """For each character here: their share of the characters' lines so far (percent), and how many
    lines (hers and theirs) since they last spoke, or None if they haven't yet."""
    talk = [e for e in evs if e["kind"] in ("you", "character")]
    theirs = [e for e in talk if e["kind"] == "character"]
    out = {}
    for c in here:
        mine = [i for i, e in enumerate(talk) if e["kind"] == "character" and e["character_id"] == c["id"]]
        share = round(100 * len(mine) / len(theirs)) if theirs else 0
        out[c["id"]] = (share, len(talk) - 1 - mine[-1] if mine else None)
    return out


async def _pick(scene_id: int, *, more: bool) -> list[tuple[int, str]]:
    with db.connect() as d:
        story, scene = story_of(d, scene_id)
        here = present(d, scene_id)
        if not here:
            return []
        most = 1 if more else int(db.setting(d, "round") or 3)
        evs = events(d, scene_id)
        who = names(d)
        ref = helper_model(d, story)
    last = evs[-1] if evs else None
    if last and last["kind"] == "you" and not more:
        named = mentioned(last["content"], here)
        if named:
            return [(cid, "Named in your line") for cid in named[:most]]
    stats = turn_stats(evs, here)
    quiet = lambda cid: "Hasn't spoken yet" if stats[cid][1] is None else f"Quiet for {stats[cid][1]} lines"
    if len(here) == 1:
        return [(here[0]["id"], "The only one here")]
    last_speaker = next((e["character_id"] for e in reversed(evs) if e["kind"] == "character"), None)
    if ref:
        people = []
        for c in here:
            share, since = stats[c["id"]]
            gap = "hasn't spoken yet" if since is None else ("spoke last" if since == 0 else f"{since} lines since they last spoke")
            people.append(f"- {c['name']} ({share}% of the lines so far, {gap}): {(c['personality'] or '').strip()[:200]}")
        recent = "\n".join(line(e, who) for e in evs[-10:]) or "(The scene hasn't started.)"
        ask = f"People in the room:\n" + "\n".join(people) + f"\n\nThe scene: {scene['setting']}\n\nThe last lines:\n{recent}"
        if more and last_speaker:
            ask += f"\n\n{who.get(last_speaker)} just spoke; pick someone else unless they'd clearly go on."
        try:
            reply = await models.complete(ref, PICK_SYSTEM.format(most=most), [{"role": "user", "content": ask}])
            if reply.strip().upper().startswith("NOBODY"):
                return []
            order: list[tuple[int, str]] = []
            for ln in reply.splitlines():
                m = re.split(r"\s+[-–—:]\s+", ln.strip(), maxsplit=1)
                why = m[1].strip().strip(".") if len(m) > 1 else ""
                for cid in mentioned(m[0], here):          # usually one name; several if it lists them
                    if cid not in [c for c, _ in order]:
                        order.append((cid, (why[:1].upper() + why[1:])[:80] if why else quiet(cid)))
            if order:
                return order[:most]
        except ModelError as e:
            log.info("pick: %s", e.code)
    # No helper, or it didn't say: whoever has gone longest without speaking.
    spoke = {}
    for e in evs:
        if e["kind"] == "character":
            spoke[e["character_id"]] = e["seq"]
    first = min(here, key=lambda c: spoke.get(c["id"], -1))["id"]
    return [(first, quiet(first))]


# --- Memory -----------------------------------------------------------------------------------

def _notes(text: str) -> list[str]:
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        m = re.match(r"^(?:[-•*]|\d+[.)])\s+(.*)", s)
        if m:
            out.append(m.group(1).strip())
    if not out:
        out = [s.strip() for s in text.split("\n") if s.strip()]
    return [n for n in out if len(n) > 3][:10]


async def condense(scene_id: int, cid: int, upto: int | None = None):
    """Write down what this character remembers of the scene, up to a seq (default: everything)."""
    async with _lock("condense", scene_id, cid):
        with db.connect() as d:
            story, scene = story_of(d, scene_id)
            if scene.get("whatif"):          # a "what if" scene leaves no memories until it's made to count
                return
            ch = character(d, cid)
            done = d.execute("select upto from condensed where scene_id = ? and character_id = ?", (scene_id, cid)).fetchone()
            start = done["upto"] if done else 0
            evs = [e for e in seen_by(events(d, scene_id), cid, story) if e["seq"] > start and (upto is None or e["seq"] <= upto)]
            last = evs[-1]["seq"] if evs else None
            spoken = [e for e in evs if e["kind"] in ("you", "character", "doc")]
            ref = helper_model(d, story)
            who = names(d)
        if last is None:
            return
        if not spoken or not ref:
            _mark(scene_id, cid, last)
            return
        lines = []
        for e in evs:
            lines.append(line(e, who))
            if e["kind"] == "character" and e["character_id"] == cid and e["inner"]:
                lines.append(f"({ch['name']} felt: {e['inner']})")
        with db.connect() as d:
            known = _known(d, story, ch, " ".join(e["content"] for e in spoken))
            mine = [r["text"] for r in d.execute("select text from memory where story_id = ? and character_id = ? "
                                                 "and replaced_by is null", (story["id"], cid))]
        body = ""
        if known:
            body = f"What {ch['name']} already remembers:\n" + "\n".join(f"[m{m['id']}] {m['text']}" for m in known) + "\n\n"
        body += f"Scene: {scene['title'] or 'Untitled'}\n{scene['setting']}\n\n" + "\n".join(lines)
        try:
            text = await models.complete(ref, MEMORY_SYSTEM.format(name=ch["name"]), [{"role": "user", "content": body}])
        except ModelError as e:
            log.warning("condense: %s %s", e.code, e.detail)
            return
        replaceable = {m["id"] for m in known}
        notes = []
        with db.connect() as d:
            for n in _notes(text):
                old = None
                m = re.search(r"\s*\(replaces?\s+\[?m?(\d+)\]?\)\s*\.?$", n, re.I)
                if m:
                    n, old = n[:m.start()].rstrip(), int(m.group(1))
                    old = old if old in replaceable else None
                if not n or any(same_memory(n, t) for t in mine):
                    continue
                new = d.execute("insert into memory(character_id, story_id, scene_id, text, from_seq, to_seq) values (?, ?, ?, ?, ?, ?)",
                                (cid, story["id"], scene_id, n, start + 1, last)).lastrowid
                if old:
                    d.execute("update memory set replaced_by = ? where id = ? and replaced_by is null", (new, old))
                mine.append(n)
                notes.append(n)
            cool(d, story["id"], cid)
        _mark(scene_id, cid, last)
        if notes:
            await update_learned(story["id"], cid, notes)


def _known(d, story: dict, ch: dict, text: str, most: int = 14) -> list[dict]:
    """What the memory-keeper should see before writing more: the memories that match these lines, and
    the newest ones, none that have been replaced."""
    hits = recall(d, story, {**ch}, text, set(), 8) if text.strip() else []
    hits = [m for m in hits if m["character_id"] == ch["id"]]
    recent = db.rows(d.execute("select * from memory where story_id = ? and character_id = ? and replaced_by is null "
                               "order by id desc limit 8", (story["id"], ch["id"])))
    out, seen = [], set()
    for m in hits + recent:
        if m["id"] not in seen:
            seen.add(m["id"])
            out.append(m)
    return sorted(out, key=lambda m: m["id"])[:most]


def forget_lines(d, scene_id: int, seq: int, through: int | None = None):
    """Lines taken back (from seq on, or just seq..through): the memories written from them go, anything
    they replaced comes back, and what's left of those lines can be written down again."""
    q = "select * from memory where scene_id = ? and to_seq >= ?" + (" and from_seq <= ?" if through is not None else "")
    args = (scene_id, seq, through) if through is not None else (scene_id, seq)
    for m in db.rows(d.execute(q, args)):
        d.execute("update memory set replaced_by = null where replaced_by = ?", (m["id"],))
        d.execute("delete from memory where id = ?", (m["id"],))
        d.execute("update condensed set upto = min(upto, ?) where scene_id = ? and character_id = ?",
                  ((m["from_seq"] or 1) - 1, scene_id, m["character_id"]))


def _mark(scene_id: int, cid: int, upto: int):
    with db.connect() as d:
        d.execute("insert into condensed(scene_id, character_id, upto) values (?, ?, ?) "
                  "on conflict(scene_id, character_id) do update set upto = max(upto, excluded.upto)", (scene_id, cid, upto))


async def update_learned(story_id: int, cid: int, notes: list[str]):
    with db.connect() as d:
        ch = character(d, cid)
        story = db.row(d.execute("select * from story where id = ?", (story_id,)).fetchone())
        cur = d.execute("select text from learned where story_id = ? and character_id = ?", (story_id, cid)).fetchone()
        ref = helper_model(d, story)
    body = f"The notes so far:\n{cur['text'] if cur and cur['text'] else '(none yet)'}\n\nNew memories:\n" + "\n".join(f"- {n}" for n in notes)
    try:
        text = await models.complete(ref, LEARNED_SYSTEM.format(name=ch["name"]), [{"role": "user", "content": body}])
    except ModelError as e:
        log.warning("learned: %s", e.code)
        return
    text = text.strip()[:2500]
    if text:
        with db.connect() as d:
            d.execute("insert into learned(story_id, character_id, text) values (?, ?, ?) on conflict(story_id, character_id) "
                      "do update set text = excluded.text, updated_at = datetime('now')", (story_id, cid, text))


async def catch_up(story_id: int, cid: int, except_scene: int | None = None):
    """Before a character speaks, make sure everything they saw in the story's other scenes is in memory."""
    with db.connect() as d:
        todo = []
        for s in d.execute("select id from scene where story_id = ? and id != ? and coalesce(whatif, 0) = 0",
                           (story_id, except_scene or 0)):
            done = d.execute("select upto from condensed where scene_id = ? and character_id = ?", (s["id"], cid)).fetchone()
            upto = done["upto"] if done else 0
            for e in d.execute("select witnesses from event where scene_id = ? and seq > ? and kind in ('you','character','doc')",
                               (s["id"], upto)):
                if cid in json.loads(e["witnesses"] or "[]"):
                    todo.append(s["id"])
                    break
    for sid in todo:
        await condense(sid, cid)


async def update_feelings(story_id: int, scene_id: int, cid: int, eid: int):
    async with _lock("feel", story_id, cid):
        with db.connect() as d:
            story, scene = story_of(d, scene_id)
            if scene.get("whatif"):
                return
            ch = character(d, cid)
            ev = db.row(d.execute("select * from event where id = ?", (eid,)).fetchone())
            if not ev:
                return
            evs = [e for e in seen_by(events(d, scene_id, ev["seq"] + 1), cid, story)][-8:]
            who = names(d)
            people = {c["id"]: c["name"] for c in cast(d, story_id) if c["id"] != cid}
            for r in story["roles"] or []:
                if r.get("name"):
                    people.setdefault(r["name"], r["name"])
            before = feeling_now(d, story_id, cid)
            ref = helper_model(d, story)
        if not ref:
            return
        was = "nothing recorded yet"
        if before:
            face = before.get("shows") or {}
            was = (before["mood"] or "") + "; " + "; ".join(
                f"{who.get(int(k), k) if str(k).isdigit() else k}: {v}" + (f" (shows: {face[str(k)]})" if face.get(str(k)) else "")
                for k, v in (before["toward"] or {}).items())
        body = (f"How {ch['name']} felt before: {was}\n\nPeople in the story: {', '.join(str(v) for v in people.values())}\n\n"
                f"The moment:\n" + "\n".join(line(e, who) for e in evs) +
                f"\n\n{ch['name']}'s private feelings just now: {ev['inner']}")
        try:
            reply = await models.complete(ref, FEELING_SYSTEM.format(name=ch["name"]), [{"role": "user", "content": body}])
        except ModelError as e:
            log.info("feelings: %s", e.code)
            return
        m = re.search(r"\{.*\}", reply, re.S)
        if not m:
            return
        try:
            obj = json.loads(m.group(0))
        except ValueError:
            return
        by_name = {str(v).lower(): k for k, v in people.items()}
        for k, v in people.items():
            by_name.setdefault(str(v).split()[0].lower(), k)
        toward, strength, shows = {}, {}, {}
        for n, v in (obj.get("toward") or {}).items():
            k = by_name.get(str(n).lower()) or by_name.get(str(n).split()[0].lower() if str(n).split() else "")
            how, much = (v.get("how"), v.get("strength")) if isinstance(v, dict) else (v, None)
            if k is not None and how:
                toward[str(k)] = str(how)[:200]
                if isinstance(v, dict) and str(v.get("shows") or "").strip():
                    shows[str(k)] = str(v["shows"]).strip()[:200]
                try:
                    strength[str(k)] = min(5, max(1, round(float(much))))
                except (TypeError, ValueError):
                    pass
        word = str(obj.get("word") or "").strip().split(" ")[0].strip(".,;:!").capitalize()[:24]
        with db.connect() as d:
            d.execute("insert into feeling(story_id, character_id, event_id, mood, toward, word, strength, shows) "
                      "values (?, ?, ?, ?, ?, ?, ?, ?)",
                      (story_id, cid, eid, str(obj.get("mood", ""))[:200], json.dumps(toward), word, json.dumps(strength),
                       json.dumps(shows)))


async def end_scene(scene_id: int):
    with db.connect() as d:
        if d.execute("select whatif from scene where id = ?", (scene_id,)).fetchone()["whatif"]:
            d.execute("update scene set state = 'ended', ended_at = datetime('now') where id = ?", (scene_id,))
            return
        everyone = set()
        for e in d.execute("select witnesses from event where scene_id = ?", (scene_id,)):
            everyone.update(json.loads(e["witnesses"] or "[]"))
        d.execute("update scene set state = 'ended', ended_at = datetime('now') where id = ?", (scene_id,))
    for cid in sorted(everyone):
        await condense(scene_id, cid)


# --- Help with writing ------------------------------------------------------------------------

DRAFT_SYSTEM = """You help a novelist sketch a character for her story. From her few words, and from anything she has already written about them, write a first draft of the rest the way she'd write it: a particular person, not a type.

- Tie every trait to something concrete: a habit, a thing they carry, how they spend money, a phrase they lean on. "Generous" is the one who always pays and remembers what everybody ordered.
- Give them two wants that pull against each other, so they can't have both.
- Give them a sore spot: a topic, a name or an object they steer away from, and how they steer.
- Not everyone is wounded. Plenty of people are content, vain, petty, cheerful or simply busy. A sore spot doesn't have to be a tragedy, unless her words point that way.
- Show how they talk with a line or two of theirs, one of them a moment where they deflect or refuse something.

What she has already written stays exactly as it is: don't repeat it or contradict it, and make what you write fit it. Answer with JSON only, with just the keys you're asked for, from these:
"pronouns": like "she/her",
"appearance": two or three sentences on how they look and carry themselves,
"personality": who they are: their history, habits and what they're like with people, 120 to 200 words, about them in the third person,
"inner_life": the two wants that pull against each other, what they fear, what they hide, and how they show or hide what they feel, 40 to 90 words,
"sore_spot": what they steer away from, and what they do when someone presses on it, a sentence or two,
"voice": how they talk, with one or two example lines, one of them deflecting or refusing,
"key_memories": two to four short facts they always carry, one per line."""

DRAFT_KEYS = ("pronouns", "appearance", "personality", "inner_life", "sore_spot", "voice", "key_memories")
DRAFT_LABELS = {"pronouns": "Pronouns", "appearance": "Appearance", "personality": "Who they are", "inner_life": "Inner life",
                "sore_spot": "Sore spot", "voice": "How they talk", "key_memories": "Always remembers"}

SUGGEST_SYSTEM = """You help a novelist keep a scene moving. {who} Write only that next turn: short, in the scene's own style, giving the characters something to react to. Don't speak or act for any of the characters. Return only the text, with no name in front and no quotation marks around the whole of it."""


def _json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        obj = json.loads(m.group(0))
    except ValueError:
        return {}
    return obj if isinstance(obj, dict) else {}


async def draft_character(cid: int, words: str, replace: bool = False) -> dict:
    """Fill in the boxes of a character's sheet that are empty, to fit the ones she has filled.
    replace: start over on all of them."""
    with db.connect() as d:
        ch = character(d, cid)
        tied = d.execute("select * from persona where id = ?", (ch.get("persona_id") or 0,)).fetchone()
        story = db.row(d.execute("select s.* from cast_member m join story s on s.id = m.story_id where m.character_id = ? "
                                 "order by s.updated_at desc limit 1", (cid,)).fetchone())
        ref = text_model(d, story, ch)
    if not ref:
        raise ModelError("setup", "no model picked")
    kept = {} if replace else {k: (ch.get(k) or "").strip() for k in DRAFT_KEYS if (ch.get(k) or "").strip()}
    todo = [k for k in DRAFT_KEYS if k not in kept]
    if not todo:
        return {}
    ask = f"Name: {ch['name']}"
    if words.strip():
        ask += f"\nHer words: {words.strip()}"
    if kept:
        ask += "\n\nWhat she has already written (keep it exactly; make the rest fit it):\n" + \
               "\n".join(f"{DRAFT_LABELS[k]}: {v}" for k, v in kept.items())
    if story and story.get("premise"):
        ask += f"\n\nThe story: {story['premise'][:1500]}"
    if tied:
        ask += f"\nShe usually plays {tied['name']} opposite this character ({tied['about']}); give them a history together."
    ask += "\n\nWrite these keys only: " + ", ".join(todo)
    reply = await models.complete(ref, DRAFT_SYSTEM, [{"role": "user", "content": ask}], effort="medium")
    obj = _json(reply)
    out = {}
    for k in todo:
        v = obj.get(k)
        if isinstance(v, list):
            v = "\n".join(str(x) for x in v)
        if v:
            out[k] = str(v).strip()
    if not out:
        raise ModelError("empty", "the draft came back empty")
    return out


async def suggest_line(scene_id: int, as_name: str = "") -> str:
    with db.connect() as d:
        story, scene = story_of(d, scene_id)
        evs = events(d, scene_id)[-30:]
        who = names(d)
        persona = db.row(d.execute("select * from persona where name = ?", (as_name,)).fetchone()) if as_name else None
        ref = text_model(d, story)
    if not ref:
        raise ModelError("setup", "no model picked")
    if persona:
        role = f"She plays {persona['name']} in it ({persona['about']}). Write {persona['name']}'s next turn: what they say and do."
    else:
        role = "She is the narrator. Write the next bit of narration: one to three sentences that move the scene on, like a small event, a detail or an entrance."
    body = (f"The story: {story['premise'][:1500]}\n\nThe scene: {scene['title']}\n{scene['setting']}\n\n"
            "So far:\n" + ("\n".join(line(e, who) for e in evs) or "(nothing yet)"))
    reply = await models.complete(ref, SUGGEST_SYSTEM.format(who=role), [{"role": "user", "content": body}], effort="low")
    text = reply.strip()
    if persona and text.lower().startswith(persona["name"].lower() + ":"):
        text = text[len(persona["name"]) + 1:].strip()
    return text


# --- Journal entries from her own pages, and from lines of a scene ----------------------------

SPLIT_SYSTEM = """You help a novelist turn her notes into journal entries for her story. An entry is one thing worth having in mind on its own: a person, a place, an object, something that happened before the story, a rule of the world, how two people stand. Answer with JSON only:
{"entries": [{"title": "a short title", "keys": ["two to five keyphrases that would come up in a scene when this matters: names, places, objects, nicknames"], "text": "the entry, in her own words wherever you can, 30 to 150 words"}]}
Keep her facts exactly as she has them and don't add any. Leave out what isn't worth keeping. Don't make two entries about the same thing."""

CHECK_SYSTEM = """You check a novelist's new journal entries for her story before she adds them. Look for three things: the same keyphrase on entries that are about different things ("duplicate"), one name spelled two ways ("spelling"), and facts that contradict each other ("contradiction"), also against what's already in her journal. Answer with JSON only:
{"issues": [{"kind": "duplicate" or "spelling" or "contradiction", "entries": [the numbers of the new entries involved], "note": "what's wrong, in one short sentence"}]}
An empty list if nothing is wrong. Don't flag anything else."""

LINES_SYSTEM = """You help a novelist keep notes on her story. From the lines she picked out of a scene, write one journal entry worth keeping: a fact, a promise, a secret, a place, how two people stand. Answer with JSON only:
{"title": "a short title", "keys": ["two to five keyphrases that would come up in a scene when this matters"], "text": "the entry, 30 to 120 words"}
or {"nothing": true} if there's nothing in them worth keeping."""


def _chunks(text: str, size: int = 8000) -> list[str]:
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if cur and len(cur) + len(para) > size:
            out.append(cur)
            cur = ""
        cur += ("\n\n" if cur else "") + para[:size * 2]
    if cur.strip():
        out.append(cur)
    return out


def _entry(v) -> dict | None:
    if not isinstance(v, dict) or not str(v.get("text") or "").strip():
        return None
    keys = v.get("keys") or []
    if isinstance(keys, str):
        keys = keys.split(",")
    return {"title": str(v.get("title") or "").strip()[:120], "keys": ", ".join(str(k).strip() for k in keys if str(k).strip())[:300],
            "text": str(v["text"]).strip()}


async def split_into_entries(text: str, story_id: int | None = None) -> dict:
    """Her pages as journal entries, and what's worth a second look before she adds them. Nothing is saved."""
    with db.connect() as d:
        story = db.row(d.execute("select * from story where id = ?", (story_id,)).fetchone()) if story_id else None
        ref = text_model(d, story) if not db.setting(d, "helper_model") else helper_model(d, story)
        have = db.rows(d.execute("select title, keys, text from journal where story_id is null" +
                                 (" or story_id = ?" if story_id else ""), (story_id,) if story_id else ()))
    if not ref:
        raise ModelError("setup", "no model picked")
    entries: list[dict] = []
    for part in _chunks(text):
        reply = await models.complete(ref, SPLIT_SYSTEM, [{"role": "user", "content": part}], effort="low")
        for v in (_json(reply).get("entries") or []):
            e = _entry(v)
            if e:
                entries.append(e)
    if not entries:
        raise ModelError("empty", "no entries came back")
    issues = []
    if len(entries) > 1 or have:
        body = "New entries:\n" + "\n".join(f"{i}. {e['title']} [{e['keys']}]: {e['text']}" for i, e in enumerate(entries, 1))
        if have:
            body += "\n\nAlready in the journal:\n" + "\n".join(f"- {h['title']} [{h['keys']}]: {h['text'][:300]}" for h in have[:60])
        try:
            reply = await models.complete(ref, CHECK_SYSTEM, [{"role": "user", "content": body}], effort="low")
            for v in (_json(reply).get("issues") or []):
                if not isinstance(v, dict) or v.get("kind") not in ("duplicate", "spelling", "contradiction"):
                    continue
                nums = sorted({int(n) - 1 for n in (v.get("entries") or []) if str(n).isdigit() and 0 < int(n) <= len(entries)})
                if nums:
                    issues.append({"kind": v["kind"], "entries": nums, "note": str(v.get("note") or "").strip()[:240]})
        except ModelError as e:
            log.info("journal check: %s", e.code)
    return {"entries": entries, "issues": issues}


async def entry_from_lines(scene_id: int, event_ids: list[int]) -> dict:
    """One journal entry from the lines she picked, or {"nothing": True}."""
    with db.connect() as d:
        story, scene = story_of(d, scene_id)
        who = names(d)
        evs = [e for e in events(d, scene_id) if e["id"] in set(event_ids)]
        ref = text_model(d, story) if not db.setting(d, "helper_model") else helper_model(d, story)
    if not evs:
        return {"nothing": True}
    if not ref:
        raise ModelError("setup", "no model picked")
    body = f"The story: {story['title']}\nThe scene: {scene['title'] or 'Untitled'}. {scene['setting']}\n\nThe lines:\n" + \
           "\n".join(line(e, who) for e in evs)
    obj = _json(await models.complete(ref, LINES_SYSTEM, [{"role": "user", "content": body}], effort="low"))
    e = None if obj.get("nothing") else _entry(obj)
    return {"entry": e} if e else {"nothing": True}
