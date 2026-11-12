# Bamah for Windows

A window around a Bamah server, in C# and WinUI 3 with the page in WebView2. The page is the whole interface; this adds a Mica title bar with the menus, the way Windows 11's own apps have them, and what a browser tab can't do well. What it looks like to use is in [docs/apps.md](../docs/apps.md).

- `Bamah/MainWindow.xaml.cs`: one window, its title bar and menus, the web view, the Save dialog for downloads, links, and the page's messages. `Settings.cs`: the address and the window's size, in `%LOCALAPPDATA%\Bamah\settings.json`, beside the web view's data (the sign-in) and `log.txt`.
- The menus call the page's commands, `window.bamahCommand(name)` in `app/bamah/static/app.js`. The page hears the Ctrl keys itself, since the web view has the keyboard, and the menus only show them.
- The page tells the window things through `window.chrome.webview.postMessage`: `look` (light or dark), `replied` (to flash the taskbar when the window isn't in front), and `window` (close, full screen).

## Building

It builds on Windows with the .NET 10 SDK:

```powershell
dotnet publish windows/Bamah/Bamah.csproj -c Release -r win-x64 -p:Platform=x64 -o build/Bamah
build\Bamah\Bamah.exe
```

`-p:BamahDefaultServer=https://…` builds in the address offered the first time. The Windows workflow (`.github/workflows/windows.yml`) builds it on GitHub's Windows machines, runs the self-test against a Bamah started on the same machine (`windows/tools/seed.py` gives it a story), and makes the installer (`installer.iss`, Inno Setup) and a portable zip, kept with the run. A tag `vX.Y.Z` (the `<Version>` in `Bamah.csproj`) also makes the GitHub release, and the Mac zip joins it ([mac/README.md](../mac/README.md#releasing)).

## Testing

```powershell
build\Bamah\Bamah.exe --selftest C:\temp\out --server http://127.0.0.1:8498 --start '#/scene/1' --data C:\temp\data
```

It opens the page, works the menus and the page's Ctrl keys, and leaves `log.txt` and pictures in the `--selftest` folder.
