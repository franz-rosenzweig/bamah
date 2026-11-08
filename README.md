<p align="center">
  <img src="app/bamah/static/icon.svg" width="110" alt="">
</p>
<h1 align="center">Bamah</h1>
<p align="center"><b>A stage for the characters of a story.</b><br>Put them in a scene together, set what's going on, and watch how each of them reacts, with any AI model you like.</p>
<p align="center">
  <img src="https://img.shields.io/badge/web-app-8c3a2b?style=flat-square" alt="Web app">
  <img src="https://img.shields.io/badge/models-any-8c3a2b?style=flat-square" alt="Any model">
  <img src="https://img.shields.io/badge/license-MIT-555555?style=flat-square" alt="MIT license">
</p>

## Why I made it

A lot of writers get to know their characters by letting them loose. You don't hand a character a script, you give them a general idea of who they are, their strengths and weaknesses, drop them into a situation, and see what they'd actually do. The good surprises, and the funny ones, are where the ideas come from.

The AI companion apps are good at one character at a time, but they're expensive, and they're bad at the thing a writer needs most: a group. Put three characters in a room, then move one of them somewhere else, and the memory of what happened in that room gets lost. So Bamah (בָּמָה, Hebrew for a stage) keeps one running story, and every line in it remembers who was in the room. A character who walks into another scene takes their memory with them, and nobody knows what they weren't there for.

## What it does

- **Loose characters:** each one is a sheet in your own words: who they are, their pronouns and how they look, their inner life (what they want, what they fear, what they hide), things they always remember, how they talk, and one instruction that always wins. Stuck on a blank sheet? Type a few words and Bamah drafts the whole thing for you to argue with.
- **Their voice:** characters speak as "I" with their actions in asterisks, or in the third person, and each one can have its own style: plain talk, roleplay, or novel prose.
- **Portraits:** a picture made from the character's appearance, photographic, painted or anime, by whichever image model you pick. Every portrait is kept with the description that made it, so you can go back to an earlier one or give it to someone else.
- **Scenes with several characters:** set the scene, say who's there, and write as the narrator or as one of your personas, the people you play, which follow you from story to story. The story picks who answers (or you do, by tapping a face or naming them), and characters can come and go mid-scene. When you're stuck, one button drafts your next line.
- **"What if" scenes:** try a confrontation or a confession that nobody remembers afterwards, and make it count if you like how it went.
- **Bring in your pages:** drop in a chapter, an outline or a backstory (Word, PDF or text), into a scene where everyone there reads it, onto one character, or into the story's journal.
- **They only know what they saw:** every line records who was in the room. Move two characters to a new scene and their memories go with them. A story can also be set so everyone knows everything.
- **What they feel:** every reply starts with the character's private state (what they feel, what they want, what they're keeping to themselves), which you can read and the others can't. Bamah keeps a map of each character's mood and how they feel about each of the others, and feeds it back in, so a slight from two scenes ago is still there.
- **Memory in layers:** the scene word for word as far back as the short-term size allows, then memories written from each character's own point of view, running notes on what they've come to know in the story, and journal entries that come to mind when one of their keyphrases comes up. All of it can be read, edited and pinned.
- **Corrections that stick:** a thumbs down on a line that's out of character takes a one-line note, like "she'd never apologize first", which goes on the character's sheet for good, and the line is taken again. A thumbs up keeps a line as an example of how they sound.
- **Every take kept:** take a line again, try it with another model, continue it, edit it, or rewind the scene to any point. A repetition guard notices when a character keeps reaching for the same phrases and asks for fresh ones.
- **Ideas:** star a moment and add a note, and it goes on the Ideas list. A story exports to Markdown.
- **Easy on the eyes:** the text size and a light or dark theme are set per device, for long reading sessions.
- **Any model:** OpenRouter (hundreds of models), OpenAI, Claude, Gemini, Ollama on your own computer, anything else that speaks the OpenAI format, or your own ChatGPT plan through "Sign in with ChatGPT". Each story and each character can use a different one.

## Running it

It's one small Docker container.

```sh
cp .env.example .env              # set a password if anyone else can reach it
docker compose up -d --build      # then open http://127.0.0.1:8465
```

Then add a model in Settings. On your own computer, Ollama works with no key at all (Bamah reaches it at `host.docker.internal:11434`).

**ChatGPT plan:** Settings, then Continue with ChatGPT. OpenAI only sends you back to `http://127.0.0.1:<port>`, so on your own computer the sign-in finishes by itself. On a server, the ChatGPT tab ends on a page that doesn't load, and you paste that page's address into Bamah, once.

## How it's built

- `app/bamah/`: the app, in Python. `web.py` is the page's server (FastAPI), `engine.py` runs the scenes (the prompts, who speaks, memory and feelings), `models.py` talks to the models, `chatgpt.py` is the ChatGPT sign-in, `images.py` makes the portraits, `docs.py` reads the files you bring in, and `db.py` is the database (SQLite, with its full-text index for recalling memories). A folder called `extras` next to them, if there is one, holds add-ons for one server only, and git ignores it.
- `app/bamah/static/`: the page, in plain HTML, CSS and JavaScript.
- `app/tests/`: the tests, which run against a stand-in model.

Everything it keeps is in one folder (the database, the portraits and the ChatGPT sign-in), so nothing secret lives in this repo.

## License

MIT. See [LICENSE](LICENSE).
