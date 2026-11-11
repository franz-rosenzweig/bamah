# Bamah for the Mac

A window around a Bamah server, in Swift with the page in a WKWebView. The page is the whole interface; this adds what a browser tab can't do well. What it looks like to use is in [docs/apps.md](../docs/apps.md).

- `Bamah/BamahApp.swift`: the app; `Window.swift`: one window, its web view, the Save and Open panels, links, and the page's messages; `Menus.swift`: the menu bar; `Server.swift`: the address, asked for the first time.
- The menus call the page's commands, `window.bamahCommand(name)` in `app/bamah/static/app.js`. The page leaves the keys alone on a Mac, so each key reaches its menu item.
- The page tells the window things through `window.webkit.messageHandlers.bamah`: `look` (the side list's colour, for the title bar) and `replied` (who answered, for the Dock and a notification).
- The web view's data, and with it the sign-in, is the app's own, as in a browser. The address is kept in the app's settings (`defaults read xyz.tiresia.bamah BamahServer`).

## Building

```sh
./build.sh && open build/Bamah.app
```

It needs only the Command Line Tools (`xcode-select --install`), and builds for Apple silicon and Intel together. `BAMAH_DEFAULT_SERVER`, or a `local.env` beside the script (`BAMAH_DEFAULT_SERVER=https://…`, left out by git), is the address offered the first time. `BAMAH_SIGN` names a signing identity; without one it's signed ad hoc, which runs on the Mac that built it.

## Testing

```sh
python tools/demo.py --shots /tmp/demo-shots --serve    # a filled-in demo, in the repository
./selftest.sh http://127.0.0.1:8498 '#/scene/1'
```

`selftest.sh` builds a copy with `SelfTest/` in it, under another bundle id so your own settings stay as they are, opens the page, works the menus, and leaves `log.txt` and pictures in `build/selftest/out`.
