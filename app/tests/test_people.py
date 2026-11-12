import json
import re
import time

import pytest

from bamah import config, db, people

from .test_scenes import say, setup_story, turn


@pytest.fixture(autouse=True)
def outbox(monkeypatch):
    """Mail goes to outbox.jsonl, and every test starts with no codes and no counts."""
    monkeypatch.setenv("BAMAH_MAIL", "outbox")
    monkeypatch.setattr(config, "URL", "https://bamah.example.com")
    people._codes.clear()
    people._hits.clear()


def sent():
    f = config.DATA / "outbox.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


def code_for(app, who):
    assert app.post("/api/login/code", json={"who": who}).status_code == 200
    return re.match(r"(\d{3}) (\d{3})", sent()[-1]["text"]).expand(r"\1\2")


def sign_in(app, who, code=None, password=None):
    app.cookies.clear()
    if password is not None:
        return app.post("/api/login", json={"name": who, "password": password})
    return app.post("/api/login/verify", json={"who": who, "code": code or code_for(app, who)})


def start(app, **ada):
    """Sam sets it up; Sam invites Ada."""
    app.post("/api/people", json={"name": "Sam", "email": "sam@example.com"})
    return app.post("/api/people", json={"name": "Ada", "email": "ada@example.com", **ada}).json()


def test_the_first_person_keeps_everything_and_invites_the_next_by_email(app):
    sid, mara, ben, cleo = setup_story(app)
    assert app.get("/api/people").json()["on"] is False
    assert app.get("/api/login").json() == {"names": False, "mail": True}
    assert app.post("/api/people", json={"name": "Sam"}).status_code == 400                    # nothing to sign in with
    sam = app.post("/api/people", json={"name": "Sam", "email": "Sam@Example.com"}).json()["person"]
    assert sam["admin"] and sam["email"] == "sam@example.com"
    assert app.get("/api/people").json()["me"]["name"] == "Sam"                                # signed in as Sam
    assert sent() == []                                                                       # nobody to tell

    r = app.post("/api/people", json={"name": "Ada", "email": "ada@example.com"}).json()
    assert r["invited"] and not r["person"]["joined"]
    mail = sent()[-1]
    assert mail["to"] == "ada@example.com" and mail["subject"] == "Your own profile on Bamah"
    assert "https://bamah.example.com" in mail["text"] and "ada@example.com" in mail["text"]
    assert "Everything that was in mine" in mail["text"] and "Sam" in mail["text"]           # signed by who invited
    assert "Open Bamah" in mail["html"]
    assert app.post("/api/people", json={"name": "ada", "email": "x@example.com"}).status_code == 409   # name taken
    assert app.post("/api/people", json={"name": "Bea", "email": "ADA@example.com"}).status_code == 409  # email taken
    assert app.post("/api/people", json={"name": "Bea", "email": "nope"}).status_code == 400
    assert app.post("/api/people", json={"name": "a@b", "email": "bea@example.com"}).status_code == 400

    # Ada signs in with a code, sees the same stories, and what she adds is hers alone
    assert sign_in(app, "ada@example.com").status_code == 200
    assert {s["id"] for s in app.get("/api/stories").json()} >= {sid}
    app.post("/api/stories", json={"title": "Only Ada's"})
    assert sign_in(app, "Sam").status_code == 200                                             # a name works too
    assert "Only Ada's" not in [s["title"] for s in app.get("/api/stories").json()]
    assert [p["joined"] for p in app.get("/api/people").json()["people"]] == [True, True]


def test_codes_are_checked_and_run_out(app):
    start(app)
    app.cookies.clear()
    assert app.get("/api/stories").status_code == 401
    assert app.get("/", follow_redirects=False).headers["location"] == "/login"
    assert app.post("/api/login/code", json={"who": "nobody"}).status_code == 404
    r = app.post("/api/login/code", json={"who": "ada"})
    assert r.json() == {"to": "a•••@example.com"}
    right = re.match(r"(\d{3}) (\d{3})", sent()[-1]["text"]).expand(r"\1\2")
    wrong = "000000" if right != "000000" else "111111"
    for _ in range(4):
        assert app.post("/api/login/verify", json={"who": "ada", "code": wrong}).json()["detail"] == "wrong"
    assert app.post("/api/login/verify", json={"who": "ada", "code": wrong}).status_code == 401
    assert app.post("/api/login/verify", json={"who": "ada", "code": right}).json()["detail"] == "expired"  # 5 wrong: gone
    assert app.get("/api/stories").status_code == 401
    code_for(app, "ada")
    code_for(app, "ada")
    assert app.post("/api/login/code", json={"who": "ada"}).json()["detail"] == "throttled"   # three a quarter hour


def test_a_password_of_your_own_and_a_new_one_signs_you_out_elsewhere(app):
    start(app)
    sign_in(app, "Ada")
    assert app.put("/api/me/password", json={"password": "short"}).json()["detail"] == "short"
    old = dict(app.cookies)
    assert app.put("/api/me/password", json={"password": "a long one"}).status_code == 200
    assert app.get("/api/stories").status_code == 200                        # still signed in here
    assert app.put("/api/me/password", json={"password": "another one"}).status_code == 401   # needs the current one
    app.cookies.clear()
    app.cookies.update(old)
    assert app.get("/api/stories").status_code == 401                        # but not with the cookie from before
    assert sign_in(app, "ada", password="a long one").status_code == 200
    assert sign_in(app, "ada", password="wrong one").json()["detail"] == "login"
    assert sign_in(app, "ada@example.com", password="a long one").status_code == 200
    assert app.request("DELETE", "/api/me/password", json={"current": "a long one"}).status_code == 200
    assert sign_in(app, "ada", password="a long one").status_code == 401


def test_only_the_first_invites_and_everyone_keeps_their_own_details(app):
    ada = start(app)["person"]
    sign_in(app, "Ada")
    assert [p["name"] for p in app.get("/api/people").json()["people"]] == ["Ada"]           # she sees only herself
    assert app.post("/api/people", json={"name": "Lee", "email": "lee@example.com"}).status_code == 403
    assert app.post(f"/api/people/{ada['id']}/invite").status_code == 403
    assert app.patch("/api/people/1", json={"name": "Not Sam"}).status_code == 403
    assert app.delete("/api/people/1").status_code == 403
    assert app.patch(f"/api/people/{ada['id']}", json={"name": "Ada L.", "email": "ada@other.example"}).status_code == 200
    assert app.patch(f"/api/people/{ada['id']}", json={"email": ""}).json()["detail"] == "email"   # nothing left to sign in with
    assert sign_in(app, "ada@other.example").status_code == 200
    sign_in(app, "Sam")
    assert app.post(f"/api/people/{ada['id']}/invite").json() == {"invited": True}


def test_a_person_without_stories_still_has_the_models_and_the_library(app):
    setup_story(app)
    app.put("/api/settings", json={"recall": "9"})
    with db.connect() as d:
        d.execute("insert into portrait(file, source) values ('lib.jpg', 'A painting · Public domain')")
        d.execute("insert into portrait(file) values ('hers.jpg')")
    for f in ("lib.jpg", "hers.jpg"):
        config.path("avatars", f).write_bytes(b"jpg")
    start(app)
    app.post("/api/people", json={"name": "Lee", "email": "lee@example.com", "stories": False})
    assert "It starts empty" in sent()[-1]["text"]
    sign_in(app, "Lee")
    assert app.get("/api/stories").json() == []
    assert app.get("/api/characters").json() == []
    s = app.get("/api/settings").json()
    assert s["connections"] and s["settings"]["recall"] == "9" and s["settings"]["default_model"]
    lee = people.folder(3)
    assert (lee / "avatars" / "lib.jpg").exists() and not (lee / "avatars" / "hers.jpg").exists()
    assert (people.folder(1) / "avatars" / "hers.jpg").exists()


def test_removing_someone_puts_their_folder_aside(app):
    start(app)
    assert app.delete("/api/people/1").status_code == 403                    # not yourself
    assert app.delete("/api/people/2").status_code == 200
    assert [p["name"] for p in people.load()] == ["Sam"]
    assert not people.folder(2).exists() and len(list((config.DATA / "removed").iterdir())) == 1
    assert app.post("/api/login/code", json={"who": "ada"}).status_code == 404


def test_without_mail_people_use_passwords(app, monkeypatch):
    monkeypatch.delenv("BAMAH_MAIL")
    assert app.get("/api/login").json() == {"names": False, "mail": False}
    app.post("/api/people", json={"name": "Sam", "password": "sam's own"})
    r = app.post("/api/people", json={"name": "Lee", "password": "lee's own"}).json()
    assert r["person"]["name"] == "Lee" and r["invited"] is False
    assert app.post("/api/login/code", json={"who": "Lee"}).json()["detail"] == "no-email"
    assert sign_in(app, "lee", password="lee's own").status_code == 200


def test_the_old_password_works_until_there_are_people(app, monkeypatch):
    monkeypatch.setattr(config, "PASSWORD", "shared")
    app.cookies.clear()
    assert app.get("/api/stories").status_code == 401
    assert app.post("/api/login", json={"password": "shared"}).status_code == 200
    assert app.get("/api/stories").status_code == 200
    app.post("/api/people", json={"name": "Sam", "email": "sam@example.com"})
    old = {"bamah": app.cookies.get("bamah")}
    assert sign_in(app, "", password="shared").status_code == 401             # the shared password is done with
    app.cookies.update(old)
    assert app.get("/api/stories").status_code == 200                         # Sam's own cookie, from setting it up


def test_someone_made_before_emails_signs_in_with_their_password(app):
    """Profiles made before invites by email have a name and a password and no email."""
    people._save([{"id": 1, "name": "Sam", "password": people._hash("four"), "admin": True, "gen": 0, "added": "x"}])
    people.folder(1).mkdir(parents=True)
    db.init(people.folder(1))
    assert sign_in(app, "sam", password="four").status_code == 200
    me = app.get("/api/people").json()["me"]
    assert me["email"] is None and me["password"]
    assert app.patch("/api/people/1", json={"email": "sam@example.com"}).status_code == 200
    assert sign_in(app, "sam@example.com").status_code == 200


def test_a_scene_and_what_comes_after_it_stay_in_the_folder_of_whoever_played_it(app):
    sid, mara, ben, cleo = setup_story(app)
    sc = app.post(f"/api/stories/{sid}/scenes", json={"characters": [mara, ben]}).json()["id"]
    lines = lambda home: len(db.connect(home).execute("select * from event where scene_id = ?", (sc,)).fetchall())
    before = lines(config.DATA)                                  # who came in, from opening the scene
    start(app)
    sign_in(app, "Ada")
    say(app, sc, "Ben lied to you, Mara.")
    turn(app, sc, mara)
    for _ in range(60):                                          # feelings are written after the reply, on their own
        if app.get(f"/api/stories/{sid}").json()["feelings"].get(str(mara)):
            break
        time.sleep(0.05)
    assert app.get(f"/api/stories/{sid}").json()["feelings"][str(mara)]["mood"] == "prickly"
    assert lines(people.folder(2)) >= before + 2
    assert lines(people.folder(1)) == before and lines(config.DATA) == before
    sign_in(app, "Sam")
    assert not app.get(f"/api/stories/{sid}").json()["feelings"].get(str(mara))
