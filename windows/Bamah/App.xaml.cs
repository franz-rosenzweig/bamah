using System.Reflection;
using Microsoft.UI.Xaml;
using Microsoft.Web.WebView2.Core;

namespace Bamah;

/// <summary>
/// Bamah for Windows: a window around the Bamah she already uses, under a Mica title bar with
/// the menus, the way a Windows 11 app has them. The page is the whole interface; nothing of hers
/// is kept here but the sign-in and which server it is (README.md). The Mac's is mac/Bamah.
/// </summary>
public partial class App : Application
{
    public static Options Options { get; private set; } = new();

    /// <summary>The settings, the web view's data (her sign-in) and the log: %LOCALAPPDATA%\Bamah, or --data.</summary>
    public static string DataDir { get; private set; } = "";

    public static string Version { get; } =
        typeof(App).Assembly.GetName().Version is { } v ? $"{v.Major}.{v.Minor}.{v.Build}" : "0";

    /// <summary>The address offered the first time, if this build was given one.</summary>
    public static string BuiltInServer { get; } =
        typeof(App).Assembly.GetCustomAttributes<AssemblyMetadataAttribute>().FirstOrDefault(a => a.Key == "BamahDefaultServer")?.Value ?? "";

    static Task<CoreWebView2Environment>? web;

    /// <summary>One WebView2 environment for every window, with Windows 11's thin scrollbars.</summary>
    public static Task<CoreWebView2Environment> WebEnvironment =>
        web ??= CoreWebView2Environment.CreateWithOptionsAsync("", Path.Join(DataDir, "WebView2"),
            new CoreWebView2EnvironmentOptions { ScrollBarStyle = CoreWebView2ScrollbarStyle.FluentOverlay }).AsTask();

    public App()
    {
        InitializeComponent();
        UnhandledException += (_, e) => Log.Write($"unhandled: {e.Exception}");
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        Options = Options.Parse(Environment.GetCommandLineArgs().Skip(1).ToArray());
        DataDir = Options.Data ?? Path.Join(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Bamah");
        Directory.CreateDirectory(DataDir);
        // no white flash before the page has drawn, in a dark theme
        Environment.SetEnvironmentVariable("WEBVIEW2_DEFAULT_BACKGROUND_COLOR", "0");
        Settings.Load();
        MainWindow.Open();
    }
}

/// <summary>--server URL (this run only), --start #/scene/1, --data DIR, --selftest DIR.</summary>
public sealed class Options
{
    public string? Server, Start, Data, SelfTest;

    public static Options Parse(string[] args)
    {
        var o = new Options();
        for (var i = 0; i < args.Length; i++)
        {
            string? Next() => i + 1 < args.Length ? args[++i] : null;
            switch (args[i])
            {
                case "--server": o.Server = Next(); break;
                case "--start": o.Start = Next(); break;
                case "--data": o.Data = Next(); break;
                case "--selftest": o.SelfTest = Next(); break;
            }
        }
        return o;
    }
}

static class Log
{
    public static void Write(string line)
    {
        try { File.AppendAllText(Path.Join(App.DataDir, "log.txt"), $"{DateTime.Now:s} {line}\n"); }
        catch (Exception) { }
    }
}
