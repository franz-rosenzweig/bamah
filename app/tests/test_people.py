import time

from bamah import config, db, people

from .test_scenes import say, setup_story, turn


def sign_in(app, name, password):
    app.cookies.clear()
    return app.post("/api/login", json={"name": name, "password": password})


def test_the_first_person_keeps_everything_and_the_next_gets_a_copy(app):
    sid, mara, ben, cleo = setup_story(app)
    assert app.get("/api/people").json() == {"on": False, "me": None, "people": []}
    assert app.get("/api/login").json() == {"names": False}

    sam = app.post("/api/people", json={"name": "Sam", "password": "four"}).json()["person"]
    assert sam["admin"]
    who = app.get("/api/people").json()
    assert who["on"] and who["me"]["name"] == "Sam"                      # whoever set it up is signed in as them
    assert [s["title"] for s in app.get("/api/stories").json()] != []
    assert app.get("/api/login").json() == {"names": True}

    ada = app.post("/api/people", json={"name": "Ada", "password": "secret"}).json()["person"]
    assert not ada["admin"]
    mine = app.get("/api/settings").json()
    assert app.post("/api/people", json={"name": "ada", "password": "other"}).status_code == 400   # taken
    assert app.post("/api/people", json={"name": "Lee", "password": "abc"}).status_code == 400     # too short

    # each is on their own: a new story of Ada's isn't Sam's
    assert sign_in(app, " ada ", "secret").status_code == 200
    assert {s["id"] for s in app.get("/api/stories").json()} >= {sid}
    assert app.get("/api/settings").json()["connections"] == mine["connections"]    # the same models, keys and all
    app.post("/api/stories", json={"title": "Only Ada's"})
    assert sign_in(app, "Sam", "four").status_code == 200
    assert "Only Ada's" not in [s["title"] for s in app.get("/api/stories").json()]
    assert (config.DATA / "people" / "2" / "bamah.db").exists()


def test_signing_in_needs_the_name_and_the_password(app):
    app.post("/api/people", json={"name": "Sam", "password": "four"})
    app.post("/api/people", json={"name": "Ada", "password": "secret"})
    app.cookies.clear()
    assert app.get("/api/stories").status_code == 401
    assert app.get("/", follow_redirects=False).headers["location"] == "/login"
    assert sign_in(app, "Ada", "four").status_code == 403
    assert sign_in(app, "Nobody", "secret").status_code == 403
    assert sign_in(app, "", "").status_code == 403
    assert app.get("/api/stories").status_code == 401


def test_only_the_first_adds_people_and_a_new_password_signs_out_elsewhere(app):
    app.post("/api/people", json={"name": "Sam", "password": "four"})
    ada = app.post("/api/people", json={"name": "Ada", "password": "secret"}).json()["person"]
    sign_in(app, "Ada", "secret")
    assert [p["name"] for p in app.get("/api/people").json()["people"]] == ["Ada"]    # she sees only herself
    assert app.post("/api/people", json={"name": "Lee", "password": "lee1"}).status_code == 403
    assert app.patch("/api/people/1", json={"password": "hers"}).status_code == 403
    assert app.delete("/api/people/1").status_code == 403

    old = dict(app.cookies)
    assert app.patch(f"/api/people/{ada['id']}", json={"password": "newer"}).status_code == 200
    assert app.get("/api/stories").status_code == 200            # still signed in here
    app.cookies.clear()
    app.cookies.update(old)
    assert app.get("/api/stories").status_code == 401            # but not with the cookie from before
    assert sign_in(app, "Ada", "newer").status_code == 200


def test_a_person_without_stories_still_has_the_models_and_the_library(app):
    setup_story(app)
    app.put("/api/settings", json={"recall": "9"})
    with db.connect() as d:
        d.execute("insert into portrait(file, source) values ('lib.jpg', 'A painting · Public domain')")
        d.execute("insert into portrait(file) values ('hers.jpg')")
    for f in ("lib.jpg", "hers.jpg"):
        config.path("avatars", f).write_bytes(b"jpg")
    app.post("/api/people", json={"name": "Sam", "password": "four"})
    app.post("/api/people", json={"name": "Lee", "password": "lee1", "stories": False})
    sign_in(app, "Lee", "lee1")
    assert app.get("/api/stories").json() == []
    assert app.get("/api/characters").json() == []
    s = app.get("/api/settings").json()
    assert s["connections"] and s["settings"]["recall"] == "9" and s["settings"]["default_model"]
    lee = people.folder(2)
    assert (lee / "avatars" / "lib.jpg").exists() and not (lee / "avatars" / "hers.jpg").exists()
    sign_in(app, "Sam", "four")
    assert (people.folder(1) / "avatars" / "hers.jpg").exists()


def test_removing_someone_puts_their_folder_aside(app):
    app.post("/api/people", json={"name": "Sam", "password": "four"})
    app.post("/api/people", json={"name": "Ada", "password": "secret"})
    assert app.delete("/api/people/1").status_code == 403        # not yourself
    assert app.delete("/api/people/2").status_code == 200
    assert [p["name"] for p in people.load()] == ["Sam"]
    assert not people.folder(2).exists() and len(list((config.DATA / "removed").iterdir())) == 1
    assert sign_in(app, "Ada", "secret").status_code == 403


def test_the_old_password_works_until_there_are_people(app, monkeypatch):
    monkeypatch.setattr(config, "PASSWORD", "shared")
    app.cookies.clear()
    assert app.get("/api/stories").status_code == 401
    assert app.post("/api/login", json={"password": "shared"}).status_code == 200
    assert app.get("/api/stories").status_code == 200
    app.post("/api/people", json={"name": "Sam", "password": "four"})
    old = {"bamah": app.cookies.get("bamah")}
    assert sign_in(app, "", "shared").status_code == 403         # the shared password is done with
    app.cookies.update(old)
    assert app.get("/api/stories").status_code == 200            # Sam's own cookie, from setting it up


def test_a_scene_and_what_comes_after_it_stay_in_the_folder_of_whoever_played_it(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara, ben]}).json()["id"]
    lines = lambda home: len(db.connect(home).execute("select * from event where scene_id = ?", (sc,)).fetchall())
    before = lines(config.DATA)                                  # who came in, from opening the scene
    app.post("/api/people", json={"name": "Sam", "password": "four"})
    app.post("/api/people", json={"name": "Ada", "password": "secret"})
    sign_in(app, "Ada", "secret")
    say(app, sc, "Ben lied to you, Mara.")
    out = turn(app, sc, mara)
    assert any(k == "done" for k, _ in out) or out
    for _ in range(60):                                          # feelings are written after the reply, on their own
        if app.get(f"/api/stories/{sid}").json()["feelings"].get(str(mara)):
            break
        time.sleep(0.05)
    assert app.get(f"/api/stories/{sid}").json()["feelings"][str(mara)]["mood"] == "prickly"
    assert lines(people.folder(2)) >= before + 2
    assert lines(people.folder(1)) == before and lines(config.DATA) == before
    sign_in(app, "Sam", "four")
    assert not app.get(f"/api/stories/{sid}").json()["feelings"].get(str(mara))
