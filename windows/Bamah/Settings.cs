using System.Text.Json.Nodes;

namespace Bamah;

/// <summary>Which Bamah it opens, and where the window was: settings.json in App.DataDir.</summary>
static class Settings
{
    static JsonObject data = new();
    static string FilePath => Path.Join(App.DataDir, "settings.json");

    public static void Load()
    {
        try { data = JsonNode.Parse(File.ReadAllText(FilePath)) as JsonObject ?? new JsonObject(); }
        catch (Exception) { data = new JsonObject(); }
    }

    static void Save()
    {
        try
        {
            var temp = FilePath + ".tmp";
            File.WriteAllText(temp, data.ToJsonString());
            File.Move(temp, FilePath, true);
        }
        catch (Exception e) { Log.Write($"settings: {e.Message}"); }
    }

    /// <summary>The address she typed, as she typed it.</summary>
    public static string? Typed => data["server"]?.GetValue<string>();

    /// <summary>The server to open: --server for a test run, else the one she chose.</summary>
    public static Uri? Server
    {
        get => App.Options.Server is { } once ? Clean(once) : Clean(Typed ?? "");
        set { data["server"] = value?.AbsoluteUri.TrimEnd('/'); Save(); }
    }

    /// <summary>The window's size, kept between runs.</summary>
    public static (int Width, int Height)? Size
    {
        get => data["width"] is { } w && data["height"] is { } h ? (w.GetValue<int>(), h.GetValue<int>()) : null;
        set
        {
            if (value is not { } s) return;
            data["width"] = s.Width;
            data["height"] = s.Height;
            Save();
        }
    }

    /// <summary>"bamah.example.com" or "http://192.168.1.5:8465/" → a URL with a scheme and no trailing slash.</summary>
    public static Uri? Clean(string text)
    {
        var s = text.Trim();
        if (s.Length == 0) return null;
        if (!s.Contains("://")) s = "https://" + s;
        s = s.TrimEnd('/');
        return Uri.TryCreate(s, UriKind.Absolute, out var u) && (u.Scheme == "http" || u.Scheme == "https") && u.Host.Length > 0 ? u : null;
    }
}
