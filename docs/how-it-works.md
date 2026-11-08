<sub>[Bamah docs](README.md) › Under the hood</sub>

# How it works

A model doesn't remember anything between one line and the next. So before every line, Bamah puts together everything that character should have in mind, and after it, Bamah writes down what changed. This page is that, in order.

## Before a character speaks

1. **Catching up:** if they were in other scenes of this story that haven't been written into their memory yet, that happens first, from their own point of view.
2. **Who they are:** their sheet (who they are, inner life, how they talk, what they always remember, the one instruction that always wins), their pronouns and appearance, the story's premise and how it's written, the voice and style they speak in, their corrections, and a few lines of theirs that sounded right.
3. **What they know:** what they've come to know in this story, and the personas you play.
4. **The scene:** every line of this scene that they were there for, word for word, as far back as the short-term size allows.
5. **Right now:** who's in the room and what they look like, the memories and journal entries that match what's happening, how they feel and about whom, and, if they've been repeating themselves, the phrases to stay away from.
6. **The ask:** reply as this character, and start with how they feel inside, between `<inner>` tags.

The model's reply streams in. Bamah splits the private line off the front and shows it in lilac, and shows the rest as what they say.

## After they speak

- **The line is kept** with who was in the room, which model said it, and what they remembered.
- **Feelings:** the helper model reads the moment and the private line, and writes how this character feels now, and about each of the others, with how strongly.
- **Memory:** when the scene grows past the short-term size, the oldest part is written into each witness's memories. Their **Come to know** notes are kept up to date as they go.
- **Who's next:** after one of your lines, the helper model reads the room and picks who would speak, up to **Replies per round**. A character you name in your line goes first.

None of this happens in a what-if scene.

## Where it all lives

Everything is in one folder: `bamah.db` (SQLite, with a full-text index for finding memories), `avatars/` for the portraits, the key that signs the sign-in cookie, and the ChatGPT sign-in if there is one. **Backup** in Settings downloads the database's contents as one file.

<sub>Next: [Developing and running it](DEVELOPING.md)</sub>
