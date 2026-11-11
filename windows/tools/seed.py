"""A small story for the Windows self-test, on a fresh Bamah with no password:
   python windows/tools/seed.py http://127.0.0.1:8498
Waits for the server, then makes a story, two characters, a scene with a line in it, and a journal
entry. Nothing here needs a model."""
import sys
import time

import httpx

c = httpx.Client(base_url=sys.argv[1], timeout=30)
for _ in range(90):
    try:
        if c.get("/login").status_code == 200:
            break
    except httpx.TransportError:
        pass
    time.sleep(1)
else:
    raise SystemExit("no Bamah answered")

sid = c.post("/api/stories", json={"title": "The Ortiz Kitchen", "premise": "A family restaurant, the night the rain came."}).json()["id"]
mara = c.post("/api/characters", json={"name": "Mara Ortiz", "personality": "Runs the kitchen like a ship.", "story_id": sid}).json()["id"]
ben = c.post("/api/characters", json={"name": "Ben Ortiz", "personality": "Charming, and late.", "story_id": sid}).json()["id"]
sc = c.post(f"/api/stories/{sid}/scenes", json={"title": "Dinner", "setting": "The kitchen. Rain. Ben is late.",
                                                 "characters": [mara, ben]}).json()["id"]
c.post(f"/api/scenes/{sc}/say", json={"text": "Mara, the bridge.", "as": ""})
c.post("/api/journal", json={"story_id": sid, "title": "The bridge", "keys": "bridge", "text": "Closed every other Tuesday."})
print(f"story {sid}, scene {sc}")
