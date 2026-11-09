"""A demo of Bamah with a made-up story, for the pictures in the docs.

It starts a throwaway Bamah on an empty folder, with a stand-in model that answers from a script, so nothing
here talks to a real AI service or the internet. Then it walks a browser through the tour the way a new
writer would (adding a model, drafting two characters, giving them faces, making a story and a scene) and
takes a picture at every step for docs/getting-started.md. After that it fills in a fuller story for the
front page's pictures.

  python -m venv .venv && .venv/bin/pip install -r app/requirements.txt playwright
  .venv/bin/python tools/demo.py --shots docs/images             # the pictures
  .venv/bin/python tools/demo.py --serve                          # or just open it at http://127.0.0.1:8498

It uses Chrome (--chrome, or $CHROME) or Playwright's own Chromium (`playwright install chromium`).
The portraits are eight by John Singer Sargent, all public domain (tools/demo-portraits/CREDITS.md).
The story, its people and everything they say are written for the demo.
"""

import argparse
import io
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACES = Path(__file__).with_name("demo-portraits")

# --- The story ------------------------------------------------------------------------------------

PEOPLE = {
    "Mara": {"pronouns": "she/her", "appearance": "Red hair she cuts herself, badly, on purpose. Flour on her sleeves most days.",
             "personality": "Mara runs the kitchen her mother left her, and runs it like a ship. She is funny in a dry way that people mistake for coldness. She notices everything and says a tenth of it.",
             "inner_life": "Afraid she has become her mother. Proud of it, too.",
             "sore_spot": "Her mother's recipes. She changes the subject by giving someone a job to do.",
             "voice": "Short sentences. Swears in Spanish when she's tired. Never says sorry; says \"fine\" instead.",
             "key_memories": ["Burned a letter from Ben without reading it.", "Taught Cleo to make bread the winter their mother was sick."]},
    "Ben": {"pronouns": "he/him", "appearance": "Tall. Expensive shoes, scuffed. A coat that costs more than the table.",
            "personality": "Ben left the family kitchen at nineteen and came back charming. He talks his way out of everything and into most things, and he can't stand a silence.",
            "inner_life": "Ashamed of the money and of how he got it. Wants Mara to need him, once.",
            "sore_spot": "Where the money came from. He makes a joke and pays for something.",
            "voice": "Easy, warm, a joke ready. Says \"come on\" when he's losing.",
            "key_memories": ["Wrote the letter from Paris and never meant to send it."]},
    "Cleo": {"pronouns": "she/her", "appearance": "Small, quick, hair always pinned up wrong.",
             "personality": "The youngest. Cleo keeps the peace by noticing first, and rehearses every hard conversation in the mirror.",
             "inner_life": "Thinks she's the reason her brother and sister fight.", "voice": "Questions instead of answers.",
             "sore_spot": "Being the youngest. She goes very quiet and very polite."},
    "Odile": {"pronouns": "she/her", "appearance": "Pearls at breakfast.", "personality": "Their mother's sister. Hosts everyone, trusts no one.",
              "inner_life": "Knows what's in the letter.", "voice": "Formal, and kind only in French.",
              "sore_spot": "Paris. She switches to French and asks about the weather."},
}
FULL = {"Mara": "Mara Ortiz", "Ben": "Ben Ortiz", "Cleo": "Cleo Ortiz", "Odile": "Aunt Odile"}
WORDS = {"Mara": "proud, funny, runs her late mother's kitchen, never apologizes first",
         "Ben": "charming, always late, expensive shoes, hiding a letter"}

LINES = {
    "Mara": [("He's going to pretend nothing happened. Not this time.",
              "*I don't look up from the onions.* You're late. *The knife keeps going.* Cleo waited."),
             ("If he says traffic one more time I'll throw the pan.",
              "*I set the knife down, finally.* The bridge was closed for an hour, Ben? Funny. I drove it at eight."),
             ("Tired. Wants someone else to be the strong one, just once.",
              "*I turn the burner off and lean on the counter.* Eat. Then we talk about the letter. You and me. Not her.")],
    "Ben": [("She knows about the letter. Cleo doesn't. Keep it that way.",
             "*I hang the coat on the chair instead of the hook.* Traffic on the bridge. *I kiss Cleo's hair and don't go near Mara.* Smells good."),
            ("Cornered. Charm always worked on her once.",
             "*I laugh, a little too loud.* You checked the bridge? That's very you, Mara. *I reach for the bread, then think better of it.*"),
            ("If Cleo asks, he'll have to lie to her face.",
             "*I sit, finally.* Come on. It's dinner. Can it just be dinner?")],
    "Cleo": [("Don't make me the reason. Please not tonight.",
              "*I slide the bread toward him like a peace offering.* I didn't mind. Really. Sit, Ben, it's still warm."),
             ("Something's wrong between them, and it has a postmark.",
              "*I fold my napkin into a neat square.* What letter?")],
    "Odile": [("They think I don't know. Children.", "*I don't take off my gloves.* Bonsoir. Somebody has been crying in this kitchen.")],
}

FEEL = {   # word, mood, {who: (how they feel, how strongly, what they show)}
    "Mara": ("Coiled", "Tired of covering for him", {"Ben": ("Furious. Wants him to say it.", 5, "Cool, clipped manners"),
                                                      "Cleo": ("Protective", 3, "Brisk, bossy"), "Odile": ("Wary respect", 2, "Perfect manners")}),
    "Ben": ("Cornered", "Performing calm", {"Mara": ("Afraid of her. Respects her.", 4, "Easy jokes"),
                                            "Cleo": ("Guilty tenderness", 3, "Big-brother cheer"), "Odile": ("Avoiding her", 2, "Charm, from across the room")}),
    "Cleo": ("Anxious", "Keeping the peace", {"Mara": ("Wants her approval", 3, "Agrees with everything"),
                                              "Ben": ("Adores him", 4, "All of it"), "Odile": ("Trusts her", 3, "Openly")}),
    "Odile": ("Watchful", "Waiting for someone to slip", {"Mara": ("Sees herself in her", 3, "Nothing at all"),
                                                           "Ben": ("Disappointed", 4, "Gracious, icy"), "Cleo": ("Fond", 3, "Warmth")}),
}

NARRATOR = "Ben comes in at nine, shaking rain off a coat that cost more than the table."


def first(name: str) -> str:
    for k, v in FULL.items():
        if name in (k, v):
            return k
    return name.split()[0]


# --- A stand-in model, in the OpenAI chat format --------------------------------------------------

def stand_in():
    from fastapi import FastAPI, Request
    from fastapi.responses import StreamingResponse

    app = FastAPI()
    said: dict[str, int] = {}
    drafts = {"n": 0}

    @app.get("/v1/models")
    def models():
        return {"data": [{"id": "demo/storyteller"}, {"id": "demo/storyteller-mini"}]}

    @app.post("/v1/chat/completions")
    async def chat(req: Request):
        body = await req.json()
        system = body["messages"][0]["content"]
        last = body["messages"][-1]["content"]
        if system.startswith("You help a novelist sketch"):
            who = "Mara" if drafts["n"] % 2 == 0 else "Ben"
            drafts["n"] += 1
            out = json.dumps(PEOPLE[who])
        elif system.startswith("You help a novelist keep a scene moving"):
            out = "The phone on the wall rings, and nobody moves to answer it."
        elif system.startswith("You help a novelist keep notes"):
            out = json.dumps({"title": "The bridge", "keys": ["bridge", "traffic", "late"],
                              "text": "Ben says the bridge was closed for an hour. Mara drove it at eight and it was open. He was somewhere else."})
        elif system.startswith("You help a novelist turn her notes"):
            paras = [p.strip() for p in last.split("\n\n") if p.strip()]
            out = json.dumps({"entries": [{"title": p.split(".")[0][:40], "keys": [w for w in re.findall(r"[A-Z][a-z]+", p)][:3],
                                           "text": p} for p in paras]})
        elif system.startswith("You check a novelist's new journal entries"):
            nums = re.findall(r"^(\d+)\. .*Ortis", last, re.M)
            out = json.dumps({"issues": [{"kind": "spelling", "entries": [1, int(nums[0])], "note": "Ortiz here, Ortis there."}] if nums else []})
        elif m := re.match(r"You are playing (.+?) in a story", system):
            who = first(m.group(1))
            if "Continue" in last.splitlines()[-1]:
                out = "And don't tell me it's nothing."
            else:
                lines = LINES.get(who) or [("Wary.", f"*{m.group(1)} looks up.* Yes?")]
                inner, text = lines[said.get(who, 0) % len(lines)]
                said[who] = said.get(who, 0) + 1
                out = f"<inner>{inner}</inner>{text}"
        elif m := re.match(r"You keep the memory of (.+?), a character", system):
            out = f"- {m.group(1)} saw Ben come in late and lie about the bridge.\n- The letter came up, and nobody would say what's in it."
        elif "running notes" in system:
            out = "Relationships and growth\nDoesn't trust Ben's excuses.\nImportant facts\nThe letter came from Paris.\nOngoing threads\nWho wrote it, and why now?"
        elif m := re.search(r"say how (.+?) feels now", system):
            who = first(m.group(1))
            here = re.search(r"People in the story: (.*)", last)
            names = [n.strip() for n in (here.group(1).split(",") if here else []) if n.strip()]
            word, mood, toward = FEEL.get(who, ("Quiet", "Watching", {}))
            out = json.dumps({"word": word, "mood": mood,
                              "toward": {n: {"how": toward[first(n)][0], "strength": toward[first(n)][1], "shows": toward[first(n)][2]}
                                         for n in names if first(n) in toward}})
        elif system.startswith("You run the turn order"):
            rows = re.findall(r"^- (.+?) \(\d+% of the lines so far, ([^)]*)\)", last, re.M)
            spoke = re.search(r"\n\n(.+?) just spoke", last)
            rows = [(n, gap) for n, gap in rows if not spoke or n != spoke.group(1)]
            why = lambda gap: ("Hasn't said a word yet" if gap.startswith("hasn't") else
                               "Just spoke, and isn't done" if gap == "spoke last" else f"Quiet for {gap.split()[0]} lines")
            out = "\n".join(f"{n} - {why(gap)}" for n, gap in rows[:2]) or "NOBODY"
        else:
            out = "ready"

        async def gen():
            import asyncio
            for i in range(0, len(out), 6):
                yield f"data: {json.dumps({'choices': [{'delta': {'content': out[i:i + 6]}}]})}\n\n"
                await asyncio.sleep(0.004)
            yield "data: [DONE]\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")

    return app


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(app, port):
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            return server
        time.sleep(0.05)
    raise SystemExit(f"nothing answered on {port}")


# --- Bamah itself, on an empty folder -------------------------------------------------------------

def start_bamah(port: int, data: Path):
    os.environ["BAMAH_DATA"] = str(data)
    os.environ["BAMAH_PASSWORD"] = ""
    os.environ["BAMAH_PORT"] = str(port)
    sys.path.insert(0, str(ROOT / "app"))
    from bamah import config, db
    from bamah.web import app
    serve(app, port)
    # the portraits go into the library, the way the public-domain ones do on a real server
    with db.connect() as d:
        for f in sorted(FACES.glob("*.jpg")):
            shutil.copyfile(f, config.path("avatars", f"demo-{f.name}"))
            d.execute("insert into portrait(character_id, file, prompt, style, source) values (null, ?, '', 'painted', ?)",
                      (f"demo-{f.name}", "John Singer Sargent · Public domain"))


# --- Pictures ---------------------------------------------------------------------------------

def shoot(page, path: Path, full=False):
    """A picture of the page, as WebP, which keeps the repo small."""
    from PIL import Image
    path = path.with_suffix(".webp")
    img = Image.open(io.BytesIO(page.screenshot(full_page=full))).convert("RGB")
    img.save(path, quality=88, method=6)
    print("  ", path.name, flush=True)


def walk_the_tour(browser, base: str, model_url: str, out: Path):
    """The tour, step by step, the way a new writer would take it."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1.5)
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))

    def step(title):
        pg.wait_for_function("t => document.querySelector('.tour-t')?.textContent === t", arg=title, timeout=20000)
        pg.wait_for_timeout(700)

    def snap(name):
        shoot(pg, out / f"start-{name}.png")

    def nxt():
        pg.click(".tour-card .tour-next")

    pg.goto(base + "/")
    pg.wait_for_selector(".tour-invite .btn.primary"); pg.wait_for_timeout(700)
    snap("01-invite"); pg.click(".tour-invite .btn.primary")
    step("First, a model"); snap("02-model")
    pg.click("[data-tour=models] .btn")
    pg.wait_for_selector(".sheet input[type=password]")
    pg.fill(".sheet input[type=password]", "sk-or-v1-demo-key")
    pg.wait_for_timeout(300); shoot(pg, out / "start-03-add-model.png")
    pg.click(".sheet .seg button:has-text('Other')")
    addr = pg.locator(".sheet label.field", has_text="Address").locator("input")
    addr.fill(model_url)
    pg.locator(".sheet label.field", has_text="Name").locator("input").fill("OpenRouter")
    pg.click(".sheet .btn.primary")
    pg.wait_for_selector(".picker-list button")       # with only the one connection, the picker opens on it
    pg.wait_for_timeout(300); shoot(pg, out / "start-04-pick-model.png")
    pg.click(".picker-list button >> nth=0")

    for who in ("Mara", "Ben"):
        if who == "Mara":
            step("Your first character"); snap("05-new-character")
            pg.click("[data-tour=new-character]")
        else:
            step("Someone to talk to")
            pg.goto(base + "/#/characters"); pg.wait_for_timeout(900); snap("10-second")
            pg.click("[data-tour=new-character]")
        pg.wait_for_selector("[data-tour=draft] input")
        pg.fill("[data-tour=draft] input", WORDS[who])
        if who == "Mara":
            step("Start from a few words"); snap("06-draft")
        pg.click("[data-tour=draft] .btn")
        pg.wait_for_function("() => document.querySelector('[data-tour=who] textarea')?.value.length > 0", timeout=20000)
        pg.wait_for_timeout(900)
        pg.fill("[data-tour=name] input", FULL[who])
        if who == "Mara":
            step("Their name"); snap("07-name"); nxt()
            step("A face")
        pg.click("[data-tour=library]")
        pg.wait_for_selector(".sheet .thumb img")
        pg.wait_for_timeout(800)
        if who == "Mara":
            shoot(pg, out / "start-08-library.png")
        pg.click(f".sheet .thumb:has(img[src*='demo-{who.lower()}'])")
        pg.click(".sheet .menu button:has-text('Use')")
        pg.wait_for_selector(".bigportrait img")
        pg.wait_for_timeout(900)
        if who == "Mara":
            snap("09-face"); nxt()
            step("Who they are"); nxt()
        else:
            pg.wait_for_selector(".tour-next:not(.hidden)"); nxt()

    step("A story"); snap("11-story")
    pg.click("[data-tour=new-story]")
    step("What it’s about")
    pg.fill(".title-input", "The Ortiz Kitchen")
    pg.fill("[data-tour=premise] textarea", "Three siblings, one restaurant, and a letter from Paris that nobody will admit to reading.")
    pg.wait_for_timeout(900); snap("12-premise"); nxt()
    step("The cast"); snap("13-cast")
    for who in ("Mara", "Ben"):
        pg.click("[data-tour=cast] .chip.plain")
        pg.click(f".sheet .chip:has-text('{FULL[who]}')")
        pg.wait_for_timeout(900)
    step("A scene"); snap("14-scene")
    pg.click("[data-tour=new-scene]")
    pg.wait_for_selector(".sheet textarea")
    pg.locator(".sheet label.field", has_text="Title").locator("input").fill("Dinner")
    pg.fill(".sheet textarea", "The kitchen on Calle Ensenada. Rain. Ben is late.")
    for who in ("Mara", "Ben"):
        pg.click(f".sheet .chip:has-text('{FULL[who]}')")
    pg.wait_for_timeout(300); shoot(pg, out / "start-15-scene-sheet.png")
    pg.click(".sheet .btn.primary")
    step("Set it going")
    pg.fill("[data-tour=composer] textarea", NARRATOR)
    snap("16-first-line")
    pg.click(".send")
    step("What they don’t say")
    # the line names Ben, so he answers; Mara gets her turn from her face below
    pg.wait_for_function("() => !document.querySelector('[data-id=temp]') && document.querySelectorAll('.msg:not(.you) .acts').length >= 1", timeout=30000)
    pg.click("[data-tour=speakers] .chip:has-text('Mara')")
    pg.wait_for_function("() => !document.querySelector('[data-id=temp]') && document.querySelectorAll('.msg:not(.you) .acts').length >= 2", timeout=30000)
    pg.wait_for_timeout(1200); snap("17-inside"); nxt()
    step("When a line isn’t right"); snap("18-fix"); nxt()
    step("Who speaks next"); snap("19-speakers"); nxt()
    step("How they feel"); pg.wait_for_timeout(4500); snap("20-feelings"); nxt()
    step("What if"); snap("21-whatif"); nxt()
    step("When the scene is over"); snap("22-end"); nxt()
    step("That’s the stage"); snap("23-done"); nxt()
    ctx.close()
    if errors:
        print("page errors:", errors)


def fill_in(base: str):
    """A fuller story for the front page: four people, a longer scene, two more stories."""
    import httpx
    c = httpx.Client(base_url=base, timeout=60)
    lib = {p["file"]: p["id"] for p in c.get("/api/portraits").json()}
    people = {x["name"]: x["id"] for x in c.get("/api/characters").json()}

    def make(name, short, fields, face, model=None):
        cid = people.get(name) or c.post("/api/characters", json={"name": name}).json()["id"]
        c.patch(f"/api/characters/{cid}", json={**fields, **({"model": model} if model else {})})
        c.post(f"/api/characters/{cid}/portrait", json={"portrait_id": lib[f"demo-{face}.jpg"]})
        people[name] = cid
        return cid

    conn = c.get("/api/settings").json()["connections"][0]["id"]
    for k in ("Cleo", "Odile"):
        f = dict(PEOPLE[k]); f["key_memories"] = "\n".join(f.get("key_memories", []))
        make(FULL[k], k, f, k.lower(), f"{conn}/demo/storyteller-mini" if k == "Cleo" else None)
    story = c.get("/api/stories").json()[0]["id"]
    for k in ("Cleo", "Odile"):
        c.post(f"/api/stories/{story}/cast", json={"character_id": people[FULL[k]]})
    sc = c.get(f"/api/stories/{story}").json()["scenes"][0]["id"]
    c.post(f"/api/scenes/{sc}/presence", json={"character_id": people["Cleo Ortiz"], "here": True})

    def turn(name):
        with c.stream("POST", f"/api/scenes/{sc}/turn", json={"character_id": people[name]}) as r:
            for _ in r.iter_lines():
                pass

    turn("Cleo Ortiz")
    c.post(f"/api/scenes/{sc}/say", json={"text": "Mara, the bridge.", "as": ""})
    turn("Mara Ortiz"); turn("Ben Ortiz")
    c.post(f"/api/stories/{story}/scenes", json={"title": "Cleo's audition", "setting": "A rehearsal room downtown.", "characters": [people["Cleo Ortiz"]]})
    w = c.post(f"/api/stories/{story}/scenes", json={"title": "Mara tells her", "setting": "The walk-in fridge, door propped open.",
                                                    "characters": [people["Mara Ortiz"], people["Cleo Ortiz"]], "whatif": True}).json()["id"]
    for name, fields, face, title in [
        ("Inés Varga", {"pronouns": "she/her", "personality": "Keeps the saltworks' books. Sharp, and lonelier than she lets on."}, "ines", "Saltworks"),
        ("Teo Bellini", {"pronouns": "he/him", "personality": "Lies for fun, never for gain."}, "teo", "Saltworks"),
        ("Vera Lund", {"pronouns": "she/her", "personality": "Headmistress. Remembers every slight."}, "vera", "Winter Term"),
        ("Julian Hale", {"pronouns": "he/him", "personality": "Kind in print, cruel at dinner."}, "julian", "Winter Term"),
    ]:
        cid = make(name, name.split()[0], fields, face)
        sid = next((s["id"] for s in c.get("/api/stories").json() if s["title"] == title), None) or c.post("/api/stories", json={"title": title}).json()["id"]
        c.post(f"/api/stories/{sid}/cast", json={"character_id": cid})
    sam = c.post("/api/personas", json={"name": "Sam", "pronouns": "they/them", "about": "A regular at the restaurant."}).json()["id"]
    c.patch(f"/api/stories/{story}", json={"personas": [sam]})
    time.sleep(4)            # feelings and memories are written in the background
    return story, sc, people


def front_page(browser, base: str, out: Path, story: int, sc: int, people: dict):
    seen = "localStorage.setItem('bamah.tour.invite', 'skipped')"
    d = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
    pg = d.new_page()
    pg.goto(base + "/"); pg.evaluate(seen)
    for name, url, wait in [("hero", f"/#/scene/{sc}", 1800), ("stories", "/#/", 1000), ("characters", "/#/characters", 1400),
                            ("character", f"/#/character/{people['Mara Ortiz']}", 1400), ("feelings", f"/#/story/{story}?tab=feelings", 1200),
                            ("setup", f"/#/story/{story}?tab=setup", 1000), ("settings", "/#/settings", 1000)]:
        pg.goto(base + url); pg.wait_for_timeout(wait); shoot(pg, out / f"{name}.png")
    pg.goto(base + f"/#/character/{people['Mara Ortiz']}"); pg.wait_for_timeout(1000)
    pg.click("[data-tour=library]"); pg.wait_for_timeout(1200); shoot(pg, out / "library.png")
    pg.goto(base + "/"); pg.evaluate("localStorage.setItem('bamah.theme', 'light')")
    pg.goto(base + f"/#/scene/{sc}"); pg.reload(); pg.wait_for_timeout(1800); shoot(pg, out / "light.png")
    pg.evaluate("localStorage.setItem('bamah.theme', 'dark')")
    d.close()
    m = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True, is_mobile=True)
    pg = m.new_page()
    pg.goto(base + "/"); pg.evaluate(seen)
    pg.goto(base + f"/#/scene/{sc}"); pg.wait_for_timeout(1800); shoot(pg, out / "phone.png")
    pg.click("[data-tour=feelings-btn]"); pg.wait_for_timeout(700); shoot(pg, out / "phone-feelings.png")
    pg.goto(base + "/#/characters"); pg.wait_for_timeout(1400); shoot(pg, out / "phone-characters.png")
    m.close()
    # the icon, at the size the front page uses
    i = browser.new_context(viewport={"width": 256, "height": 256}, device_scale_factor=1)
    pg = i.new_page()
    pg.set_content(f'<body style="margin:0;background:transparent">{(ROOT / "app/bamah/static/icon.svg").read_text()}</body>')
    pg.locator("svg").evaluate("s => { s.setAttribute('width', 256); s.setAttribute('height', 256); }")
    pg.locator("svg").screenshot(path=str(out / "icon.png"), omit_background=True)
    i.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--shots", type=Path, help="take the pictures into this folder")
    ap.add_argument("--serve", action="store_true", help="fill in the story and keep it open")
    ap.add_argument("--port", type=int, default=8498)
    ap.add_argument("--chrome", default=os.environ.get("CHROME"), help="the Chrome to drive (default: Playwright's Chromium)")
    a = ap.parse_args()
    data = Path(tempfile.mkdtemp(prefix="bamah-demo-"))
    model_port = free_port()
    serve(stand_in(), model_port)
    model_url = f"http://127.0.0.1:{model_port}/v1"
    start_bamah(a.port, data)
    base = f"http://127.0.0.1:{a.port}"
    try:
        if a.shots:
            a.shots.mkdir(parents=True, exist_ok=True)
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                kw = {"executable_path": a.chrome, "chromium_sandbox": False, "args": ["--no-sandbox"]} if a.chrome else {}
                browser = p.chromium.launch(**kw)
                walk_the_tour(browser, base, model_url, a.shots)
                story, sc, people = fill_in(base)
                front_page(browser, base, a.shots, story, sc, people)
                browser.close()
        if a.serve:
            if not a.shots:
                import httpx
                httpx.post(base + "/api/connections", json={"preset": "custom", "name": "Demo", "base_url": model_url})
            print(f"Bamah's demo is at {base} (Ctrl-C to stop)")
            while True:
                time.sleep(3600)
    finally:
        shutil.rmtree(data, ignore_errors=True)


if __name__ == "__main__":
    main()
