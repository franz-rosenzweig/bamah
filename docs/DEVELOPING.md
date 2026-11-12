<sub>[Bamah docs](README.md) › Under the hood</sub>

# Developing and running it

## Running it

Bamah is one small Docker container.

```sh
cp .env.example .env              # set a password if anyone else can reach it
docker compose up -d --build      # then open http://127.0.0.1:8465
```

| Setting in `.env` | What it does |
|---|---|
| `BAMAH_PASSWORD` | the password to sign in with, until there are people (Settings › People): then each signs in with a name and password of their own. Empty means no sign-in, for a copy on your own computer. |
| `BAMAH_PORT` | the port it answers on (127.0.0.1 only). ChatGPT's sign-in comes back to this port. |
| `DATA_DIR` | the folder for the database, the portraits and the ChatGPT sign-in. |
| `BAMAH_NAME`, `TZ` | what it calls itself, and the time zone. |

Anything that only fits one server, like another address to listen on, goes in `docker-compose.override.yml`, which git ignores. On a server, put Bamah behind HTTPS (a reverse proxy or a tunnel) and set a password.

Ollama on the same computer is reached at `host.docker.internal:11434`.

## The code

- `app/bamah/web.py`: the server (FastAPI) and every route.
- `app/bamah/engine.py`: the scenes: what a character is told, who speaks, memory and feelings. See [How it works](how-it-works.md).
- `app/bamah/models.py`: talking to the models, in the OpenAI format, through the Anthropic SDK for Claude, and through the ChatGPT plan (`chatgpt.py`).
- `app/bamah/people.py`: the people who sign in. Each has a folder under `people/` in the data folder, with their own database, portraits and backgrounds; `config.path()` points at the folder of whoever the request is from. The pictures in a copy are linked, not copied, since a picture is only ever added or deleted.
- `app/bamah/images.py`: portraits. `docs.py`: reading Word, PDF and text files. `db.py`: the database and its migrations.
- `app/bamah/static/`: the page, in plain HTML, CSS and JavaScript, with no build step. The fonts (Inter and Literata, both under the SIL Open Font License) are served from `static/fonts/`.
- `app/bamah/extras/`, if there is one: add-ons for one server only. Git ignores it, and the app runs the same without it.

## The tests

```sh
cd app
pip install -r requirements.txt
python -m pytest tests
```

They run against a stand-in model that answers by what it's asked to do, so they need no key and no internet.

## The demo and the pictures

Every picture in these docs comes from `tools/demo.py`. It starts a throwaway Bamah on an empty folder with a stand-in model that answers from a script, walks a browser through the tour the way a new writer would, and takes a picture at every step. Then it fills in a fuller story for the rest.

```sh
python -m venv .venv && .venv/bin/pip install -r app/requirements.txt playwright
.venv/bin/python tools/demo.py --shots docs/images      # the pictures
.venv/bin/python tools/demo.py --serve                   # or open the demo at http://127.0.0.1:8498
```

It drives Chrome (`--chrome`, or `$CHROME`) or Playwright's own Chromium. The story, its people and everything they say are written for the demo, and the eight portraits are by John Singer Sargent, in the public domain (`tools/demo-portraits/CREDITS.md`).

<sub>Back to [the docs](README.md)</sub>
