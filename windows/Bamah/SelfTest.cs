namespace Bamah;

/// <summary>
/// --selftest DIR (with --server and --start): the page loads in the app, the menus and the page's
/// Ctrl keys reach it, and pictures land in DIR beside log.txt. The Windows workflow runs it
/// against a Bamah on the same machine.
/// </summary>
static class SelfTest
{
    public static async Task Run(MainWindow w)
    {
        var dir = App.Options.SelfTest!;
        Directory.CreateDirectory(dir);
        var lines = new List<string>();
        var failed = 0;
        void Check(bool ok, string what)
        {
            if (!ok) failed++;
            lines.Add((ok ? "ok    " : "FAIL  ") + what);
        }
        async Task<string> Js(string code) => await w.Js(code);

        try
        {
            for (var i = 0; i < 300 && !w.PageLoaded; i++) await Task.Delay(100);
            Check(w.PageLoaded, "the page loads");
            if (App.Options.Start is { } start) await Js($"location.hash = {System.Text.Json.JsonSerializer.Serialize(start)}");
            await Task.Delay(3000);
            Check((await Js("navigator.userAgent")).Contains("BamahApp/"), "the page knows it's in the app");
            Check(await Js("typeof window.bamahCommand") == "\"function\"", "the page takes commands");
            var titles = string.Join(", ", w.MenuTitles);
            Check(titles == "File, Edit, Scene, View, Help", "menus: " + titles);
            await w.Shot(Path.Join(dir, "scene.png"));
            try { await w.TitleShot(Path.Join(dir, "titlebar.png")); }
            catch (Exception e) { lines.Add($"note  no title bar picture: {e.Message}"); }

            w.Command("journal");
            await Task.Delay(900);
            Check(await Js("localStorage.getItem('bamah.side')") == "\"journal\"", "View › Journal");
            await w.Shot(Path.Join(dir, "journal.png"));

            // the page's own keys, as the Windows app has them
            await Js("document.dispatchEvent(new KeyboardEvent('keydown', {key: '1', ctrlKey: true, bubbles: true}))");
            await Task.Delay(700);
            Check(await Js("localStorage.getItem('bamah.side')") == "\"feelings\"", "Ctrl+1 opens Feelings");

            w.Command("bigger");
            await Task.Delay(400);
            Check(await Js("localStorage.getItem('bamah.size')") == "\"1.12\"", "View › Bigger");
            w.Command("actualSize");
            await Task.Delay(400);
            Check(await Js("localStorage.getItem('bamah.size')") == "\"1\"", "View › Actual size");

            w.Command("settings");
            await Task.Delay(1500);
            Check(await Js("location.hash") == "\"#/settings\"", "File › Settings");
            await w.Shot(Path.Join(dir, "settings.png"));
        }
        catch (Exception e) { Check(false, $"the self-test itself: {e}"); }

        lines.Add(failed == 0 ? "PASSED" : $"FAILED {failed}");
        File.WriteAllLines(Path.Join(dir, "log.txt"), lines);
        Environment.Exit(failed == 0 ? 0 : 1);
    }
}
