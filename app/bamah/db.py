"""The database: one SQLite file with the characters, the stories and everything that happened in them."""

import json
import sqlite3

from . import config

SCHEMA = """
create table if not exists setting(key text primary key, value text);

create table if not exists connection(
  id integer primary key,
  preset text not null,            -- openrouter, openai, anthropic, gemini, ollama, custom, chatgpt
  name text not null,
  base_url text default '',
  api_key text default '',
  created_at text default (datetime('now'))
);

create table if not exists character(
  id integer primary key,
  name text not null,
  avatar text,                     -- a file in data/avatars
  personality text default '',     -- who they are, in her words
  inner_life text default '',      -- what they want and fear, how they show or hide what they feel
  key_memories text default '',    -- facts that always go along
  voice text default '',           -- how they talk: an example or two
  directive text default '',       -- the one instruction that always wins
  model text,                      -- "connection id/model", or null for the story's
  hue integer default 0,
  created_at text default (datetime('now')),
  updated_at text default (datetime('now'))
);

-- What she has said about a character when it acted wrong. Always goes along, and always wins.
create table if not exists correction(
  id integer primary key,
  character_id integer not null references character(id) on delete cascade,
  text text not null,
  event_id integer,
  created_at text default (datetime('now'))
);

-- Lines that sounded exactly right (a thumbs up).
create table if not exists example(
  id integer primary key,
  character_id integer not null references character(id) on delete cascade,
  text text not null,
  event_id integer unique,
  created_at text default (datetime('now'))
);

create table if not exists story(
  id integer primary key,
  title text not null,
  premise text default '',         -- the world and the setup everyone shares
  directive text default '',       -- how every reply should be written
  style text default 'roleplay',   -- roleplay, narrative, dialogue
  length text default 'medium',    -- short, medium, long
  roles text default '[]',         -- who she can speak as: [{"name", "about"}]
  memory text default 'witnessed', -- witnessed: they only know what they saw; shared: everyone knows everything
  turns text default 'auto',       -- auto: the story picks who answers; manual: nobody answers until she picks
  model text,
  created_at text default (datetime('now')),
  updated_at text default (datetime('now'))
);

create table if not exists cast_member(
  story_id integer not null references story(id) on delete cascade,
  character_id integer not null references character(id) on delete cascade,
  primary key(story_id, character_id)
);

create table if not exists scene(
  id integer primary key,
  story_id integer not null references story(id) on delete cascade,
  title text default '',
  setting text default '',         -- where, when, what's going on
  seq integer default 0,           -- its place in the story
  state text default 'open',
  created_at text default (datetime('now')),
  ended_at text
);

-- Who was in a scene, and from when to when (event seq numbers).
create table if not exists presence(
  id integer primary key,
  scene_id integer not null references scene(id) on delete cascade,
  character_id integer not null references character(id) on delete cascade,
  joined_seq integer not null,
  left_seq integer
);

create table if not exists event(
  id integer primary key,
  scene_id integer not null references scene(id) on delete cascade,
  seq integer not null,
  kind text not null,              -- you, character, enter, leave
  character_id integer,
  speaker text default '',         -- for her lines: the role she spoke as
  content text default '',
  inner text default '',           -- what the character felt and kept to themselves
  versions text default '[]',      -- every take: [{"content", "inner", "model"}]
  pick integer default 0,          -- which take is showing
  model text default '',
  witnesses text default '[]',     -- the characters who were there
  recalled text default '[]',      -- the memories and journal entries that came to mind
  rating integer default 0,
  starred integer default 0,
  idea text default '',
  created_at text default (datetime('now'))
);
create index if not exists event_scene on event(scene_id, seq);

create table if not exists memory(
  id integer primary key,
  character_id integer not null references character(id) on delete cascade,
  story_id integer not null references story(id) on delete cascade,
  scene_id integer,
  text text not null,
  pinned integer default 0,
  created_at text default (datetime('now'))
);
create virtual table if not exists memory_fts using fts5(text, content='memory', content_rowid='id');
create trigger if not exists memory_ai after insert on memory begin
  insert into memory_fts(rowid, text) values (new.id, new.text);
end;
create trigger if not exists memory_ad after delete on memory begin
  insert into memory_fts(memory_fts, rowid, text) values ('delete', old.id, old.text);
end;
create trigger if not exists memory_au after update of text on memory begin
  insert into memory_fts(memory_fts, rowid, text) values ('delete', old.id, old.text);
  insert into memory_fts(rowid, text) values (new.id, new.text);
end;

-- How far each character's memory of a scene has been written down.
create table if not exists condensed(
  scene_id integer not null references scene(id) on delete cascade,
  character_id integer not null references character(id) on delete cascade,
  upto integer not null,
  primary key(scene_id, character_id)
);

-- A character's running notes for one story: relationships and growth, facts, open threads.
create table if not exists learned(
  story_id integer not null references story(id) on delete cascade,
  character_id integer not null references character(id) on delete cascade,
  text text default '',
  updated_at text default (datetime('now')),
  primary key(story_id, character_id)
);

-- How a character feels, over time: their mood, and how they feel about each of the others.
create table if not exists feeling(
  id integer primary key,
  story_id integer not null references story(id) on delete cascade,
  character_id integer not null references character(id) on delete cascade,
  event_id integer,
  mood text default '',
  toward text default '{}',        -- {"other character id": "how they feel about them"}
  created_at text default (datetime('now'))
);
create index if not exists feeling_story on feeling(story_id, character_id, id);

-- Notes that come to mind when one of their keyphrases comes up.
-- story_id and character_id both null: everywhere; story only: that story; character only: that character.
create table if not exists journal(
  id integer primary key,
  story_id integer references story(id) on delete cascade,
  character_id integer references character(id) on delete cascade,
  title text default '',
  keys text default '',            -- keyphrases, comma separated
  text text not null,
  created_at text default (datetime('now'))
);

-- People the writer plays, in any story.
create table if not exists persona(
  id integer primary key,
  name text not null,
  pronouns text default '',
  about text default '',
  created_at text default (datetime('now'))
);

-- Portraits, generated or uploaded, kept with the description that made them.
create table if not exists portrait(
  id integer primary key,
  character_id integer references character(id) on delete set null,
  file text not null,
  prompt text default '',
  style text default '',
  created_at text default (datetime('now'))
);
"""

# Columns added after the first version: (table, column, declaration).
COLUMNS = [
    ("character", "pronouns", "text default ''"),
    ("character", "appearance", "text default ''"),
    ("character", "person", "text"),          # first, third, or null for the story's
    ("character", "style", "text"),           # roleplay, narrative, dialogue, or null for the story's
    ("character", "persona_id", "integer"),   # the persona this character usually talks to
    ("story", "person", "text default 'first'"),
    ("story", "personas", "text default '[]'"),
    ("scene", "whatif", "integer default 0"),  # a scene that doesn't count: no memories, no feelings
    ("feeling", "word", "text default ''"),          # the mood in one word
    ("feeling", "strength", "text default '{}'"),    # {"other character id": 1-5}
    ("portrait", "source", "text default ''"),       # where a library portrait came from
]

DEFAULTS = {"short_term": "60000", "recall": "6", "feelings": "1", "round": "3", "repetition": "1", "thinking": "low"}


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(config.path("bamah.db"), timeout=30, isolation_level=None, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("pragma foreign_keys = on")
    db.execute("pragma journal_mode = wal")
    db.execute("pragma busy_timeout = 30000")
    return db


def init():
    with connect() as db:
        db.executescript(SCHEMA)
        for table, column, decl in COLUMNS:
            have = {r["name"] for r in db.execute(f"pragma table_info({table})")}
            if column not in have:
                db.execute(f"alter table {table} add column {column} {decl}")
        _roles_to_personas(db)


def _roles_to_personas(db):
    """Stories once kept their own list of roles; they're personas now, shared by every story."""
    for s in db.execute("select id, roles, personas from story").fetchall():
        try:
            roles = json.loads(s["roles"] or "[]")
        except ValueError:
            roles = []
        if not roles:
            continue
        ids = json.loads(s["personas"] or "[]")
        for r in roles:
            name = str(r.get("name", "")).strip()
            if not name:
                continue
            row = db.execute("select id from persona where name = ?", (name,)).fetchone()
            pid = row["id"] if row else db.execute("insert into persona(name, about) values (?, ?)",
                                                   (name, str(r.get("about", "")))).lastrowid
            if pid not in ids:
                ids.append(pid)
        db.execute("update story set personas = ?, roles = '[]' where id = ?", (json.dumps(ids), s["id"]))


def setting(db, key: str, default: str | None = None) -> str | None:
    row = db.execute("select value from setting where key = ?", (key,)).fetchone()
    if row:
        return row["value"]
    return DEFAULTS.get(key, default)


def set_setting(db, key: str, value):
    if value is None:
        db.execute("delete from setting where key = ?", (key,))
    else:
        db.execute("insert into setting(key, value) values (?, ?) on conflict(key) do update set value = excluded.value",
                   (key, str(value)))


def row(r) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in ("versions", "witnesses", "recalled", "roles", "toward", "personas", "strength"):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except ValueError:
                d[k] = {} if k in ("toward", "strength") else []
    return d


def rows(rs) -> list[dict]:
    return [row(r) for r in rs]
