using System.Runtime.InteropServices;
using System.Runtime.InteropServices.WindowsRuntime;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.UI;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Imaging;
using Microsoft.Web.WebView2.Core;
using Windows.Graphics.Imaging;
using Windows.Storage.Pickers;
using Windows.Storage.Streams;
using Windows.System;
using WinRT.Interop;

namespace Bamah;

/// <summary>
/// One Bamah window: a Mica title bar with the icon, the menus and the window's name, the
/// system's caption buttons at the right, and the page under it. The menus call the page's
/// commands (window.bamahCommand in app.js); the page has the same Ctrl keys itself.
/// </summary>
public sealed partial class MainWindow : Window
{
    public static readonly List<MainWindow> All = [];

    public IntPtr Handle { get; }
    WebView2? web;
    Uri? home;
    bool started, full;
    public bool PageLoaded { get; private set; }

    public static MainWindow Open()
    {
        var window = new MainWindow();
        All.Add(window);
        window.Activate();
        return window;
    }

    MainWindow()
    {
        InitializeComponent();
        Title = "Bamah";
        Handle = WindowNative.GetWindowHandle(this);
        var ico = Path.Join(AppContext.BaseDirectory, "Assets", "Bamah.ico");
        if (File.Exists(ico)) AppWindow.SetIcon(ico);
        var png = Path.Join(AppContext.BaseDirectory, "Assets", "icon-64.png");
        if (File.Exists(png)) AppIcon.Source = new BitmapImage(new Uri(png));
        MakeTitleBar();
        MakeMenus();
        var size = Settings.Size ?? (1280, 820);
        AppWindow.Resize(new Windows.Graphics.SizeInt32(Math.Max(800, size.Width), Math.Max(560, size.Height)));
        if (AppWindow.Presenter is OverlappedPresenter p) { p.PreferredMinimumWidth = 800; p.PreferredMinimumHeight = 560; }
        AppWindow.Changed += (_, e) => { if (e.DidSizeChange || e.DidPresenterChange) FitTitleBarSoon(); };
        Root.Loaded += async (_, _) =>
        {
            FitTitleBarSoon();
            await StartAsync();
        };
        Activated += (_, e) =>
            TitleText.Opacity = AppIcon.Opacity = e.WindowActivationState == WindowActivationState.Deactivated ? 0.5 : 1;
        Closed += (_, _) =>
        {
            if (!full && AppWindow.Presenter is OverlappedPresenter { State: OverlappedPresenterState.Restored })
                Settings.Size = (AppWindow.Size.Width, AppWindow.Size.Height);
            try { web?.Close(); } catch (Exception) { }
            All.Remove(this);
        };
    }

    // ---- the title bar ------------------------------------------------------------------

    void MakeTitleBar()
    {
        SystemBackdrop = new MicaBackdrop();
        ExtendsContentIntoTitleBar = true;
        SetTitleBar(DragArea);
        var bar = AppWindow.TitleBar;
        bar.PreferredHeightOption = TitleBarHeightOption.Tall;
        bar.ButtonBackgroundColor = Colors.Transparent;
        bar.ButtonInactiveBackgroundColor = Colors.Transparent;
        PaintCaptionButtons();
        Root.ActualThemeChanged += (_, _) => PaintCaptionButtons();
    }

    void PaintCaptionButtons()
    {
        var dark = Root.ActualTheme == ElementTheme.Dark;
        var bar = AppWindow.TitleBar;
        var ink = dark ? Colors.White : Colors.Black;
        bar.ButtonForegroundColor = bar.ButtonHoverForegroundColor = bar.ButtonPressedForegroundColor = ink;
        bar.ButtonHoverBackgroundColor = dark ? ColorHelper.FromArgb(0x15, 0xFF, 0xFF, 0xFF) : ColorHelper.FromArgb(0x09, 0, 0, 0);
        bar.ButtonPressedBackgroundColor = dark ? ColorHelper.FromArgb(0x0B, 0xFF, 0xFF, 0xFF) : ColorHelper.FromArgb(0x06, 0, 0, 0);
        bar.ButtonInactiveForegroundColor = dark ? ColorHelper.FromArgb(0x5D, 0xFF, 0xFF, 0xFF) : ColorHelper.FromArgb(0x5C, 0, 0, 0);
    }

    /// <summary>Room for the caption buttons, which the system draws over the row.</summary>
    void FitTitleBar()
    {
        if (!AppWindow.IsVisible || full || AppWindow.Presenter is OverlappedPresenter { State: OverlappedPresenterState.Minimized }) return;
        try
        {
            var scale = Root.XamlRoot?.RasterizationScale ?? GetDpiForWindow(Handle) / 96.0;
            int left = AppWindow.TitleBar.LeftInset, right = AppWindow.TitleBar.RightInset;
            if (scale <= 0 || (left <= 0 && right <= 0)) return;
            LeftPad.Width = new GridLength(Math.Max(0, left / scale));
            RightPad.Width = new GridLength(Math.Max(0, right / scale));
        }
        catch (Exception e) { Log.Write($"title bar: {e.Message}"); }
    }

    void FitTitleBarSoon() =>
        DispatcherQueue.TryEnqueue(Microsoft.UI.Dispatching.DispatcherQueuePriority.Low, FitTitleBar);

    // ---- the menus ----------------------------------------------------------------------

    readonly List<(string Title, List<string> Items)> menuList = [];

    public IEnumerable<string> MenuTitles => menuList.Select(m => m.Title);

    void MakeMenus()
    {
        Top("File",
            Page("New story", "newStory", "Ctrl+N"),
            Page("New scene", "newScene", "Ctrl+Shift+N"),
            Page("New character", "newCharacter"),
            null,
            Item("New window", () => Open()),
            Item("Server…", async () => { if (await AskServerAsync(false) is { } u) Load(u); }),
            Page("Settings", "settings", "Ctrl+,"),
            null,
            Item("Close", Close, "Ctrl+W"),
            Item("Exit", () => Application.Current.Exit()));
        Top("Edit",
            Item("Undo", () => Edit("undo"), "Ctrl+Z"),
            Item("Redo", () => Edit("redo"), "Ctrl+Y"),
            null,
            Item("Cut", () => Edit("cut"), "Ctrl+X"),
            Item("Copy", () => Edit("copy"), "Ctrl+C"),
            Item("Paste", Paste, "Ctrl+V"),
            Item("Select all", () => Edit("selectAll"), "Ctrl+A"));
        Top("Scene",
            Page("Send", "next", "Ctrl+Enter"),
            Page("Go on", "goOn", "Ctrl+]"),
            Page("Again", "again", "Ctrl+R"),
            Page("Write my line", "writeMyLine", "Ctrl+L"),
            Page("Stop", "stop"),
            null,
            Page("What if…", "whatIf", "Ctrl+Shift+W"));
        Top("View",
            Page("Feelings", "feelings", "Ctrl+1"),
            Page("Memory", "memory", "Ctrl+2"),
            Page("Journal", "journal", "Ctrl+3"),
            null,
            Page("Bigger", "bigger", "Ctrl+Plus"),
            Page("Smaller", "smaller", "Ctrl+Minus"),
            Page("Actual size", "actualSize", "Ctrl+0"),
            null,
            Item("Full screen", ToggleFullScreen, "F11"));
        Top("Help",
            Item("Bamah help", () => _ = Launcher.LaunchUriAsync(new Uri("https://docs.tiresia.xyz/bamah/"))),
            Item("About Bamah", async () => await new ContentDialog
            {
                Title = "Bamah", Content = $"Version {App.Version}", CloseButtonText = "OK", XamlRoot = Root.XamlRoot,
            }.ShowAsync()));
    }

    void Top(string title, params MenuFlyoutItemBase?[] items)
    {
        var top = new MenuBarItem { Title = title };
        var names = new List<string>();
        foreach (var it in items)
        {
            top.Items.Add(it ?? new MenuFlyoutSeparator());
            if (it is MenuFlyoutItem m) names.Add(m.Text);
        }
        Menu.Items.Add(top);
        menuList.Add((title, names));
    }

    /// <summary>An item; its key is only shown, since the page hears the key itself.</summary>
    static MenuFlyoutItem Item(string text, Action run, string? key = null)
    {
        var it = new MenuFlyoutItem { Text = text, KeyboardAcceleratorTextOverride = key ?? "" };
        it.Click += (_, _) => run();
        return it;
    }

    MenuFlyoutItem Page(string text, string command, string? key = null) => Item(text, () => Command(command), key);

    /// <summary>One of the page's commands, as its menu item or key would run it.</summary>
    public void Command(string name)
    {
        web?.Focus(FocusState.Programmatic);
        _ = Js($"window.bamahCommand && window.bamahCommand({JsonSerializer.Serialize(name)})");
    }

    void Edit(string what)
    {
        web?.Focus(FocusState.Programmatic);
        _ = Js($"document.execCommand({JsonSerializer.Serialize(what)})");
    }

    async void Paste()
    {
        try
        {
            var content = Windows.ApplicationModel.DataTransfer.Clipboard.GetContent();
            if (!content.Contains(Windows.ApplicationModel.DataTransfer.StandardDataFormats.Text)) return;
            var text = await content.GetTextAsync();
            web?.Focus(FocusState.Programmatic);
            await Js($"document.execCommand('insertText', false, {JsonSerializer.Serialize(text)})");
        }
        catch (Exception e) { Log.Write($"paste: {e.Message}"); }
    }

    public void ToggleFullScreen()
    {
        full = !full;
        AppWindow.SetPresenter(full ? AppWindowPresenterKind.FullScreen : AppWindowPresenterKind.Overlapped);
        TitleRow.Visibility = full ? Visibility.Collapsed : Visibility.Visible;
        if (!full) FitTitleBarSoon();
    }

    // ---- the page -----------------------------------------------------------------------

    async Task StartAsync()
    {
        if (started) return;
        started = true;
        var server = Settings.Server ?? await AskServerAsync(true);
        if (server == null)
        {
            if (All.Count > 1) Close(); else Application.Current.Exit();
            return;
        }
        CoreWebView2Environment environment;
        try { environment = await App.WebEnvironment; }
        catch (Exception e)
        {
            Log.Write($"no WebView2: {e}");
            Problem("Bamah needs the Microsoft Edge WebView2 Runtime", "https://go.microsoft.com/fwlink/p/?LinkId=2124703");
            return;
        }
        var view = new WebView2();
        Grid.SetRow(view, 1);
        Root.Children.Add(view);
        web = view;
        await view.EnsureCoreWebView2Async(environment);
        var core = view.CoreWebView2;
        var s = core.Settings;
        s.AreBrowserAcceleratorKeysEnabled = false;      // Ctrl+R, Ctrl+L… are the page's keys here, not the browser's
        s.IsStatusBarEnabled = false;
        s.IsPinchZoomEnabled = false;
        s.IsSwipeNavigationEnabled = false;
        s.IsPasswordAutosaveEnabled = true;
        s.AreDevToolsEnabled = App.Options.SelfTest != null;
        s.UserAgent = $"{s.UserAgent} BamahApp/{App.Version}";
        core.WebMessageReceived += OnMessage;
        core.NavigationStarting += OnNavigationStarting;
        core.NavigationCompleted += OnNavigationCompleted;
        core.NewWindowRequested += OnNewWindowRequested;
        core.DownloadStarting += OnDownloadStarting;
        core.ProcessFailed += (_, _) => core.Reload();
        core.DocumentTitleChanged += (_, _) => Title = TitleText.Text = string.IsNullOrEmpty(core.DocumentTitle) ? "Bamah" : core.DocumentTitle;
        Load(server);
        if (App.Options.SelfTest != null && All.Count == 1) await SelfTest.Run(this);
    }

    void Load(Uri url)
    {
        home = url;
        PageLoaded = false;
        web?.CoreWebView2?.Navigate(url.AbsoluteUri);
    }

    bool SameSite(Uri url) => home != null && url.Host.Equals(home.Host, StringComparison.OrdinalIgnoreCase) && url.Port == home.Port;

    /// <summary>A link to another site opens in the browser; a redirect (a sign-in page in front of the server) stays.</summary>
    void OnNavigationStarting(CoreWebView2 sender, CoreWebView2NavigationStartingEventArgs e)
    {
        if (!Uri.TryCreate(e.Uri, UriKind.Absolute, out var url) || url.Scheme is "about" or "data" or "blob" || SameSite(url)) return;
        if (!e.IsUserInitiated) return;
        e.Cancel = true;
        if (url.Scheme is "http" or "https" or "mailto") _ = Launcher.LaunchUriAsync(url);
    }

    void OnNewWindowRequested(CoreWebView2 sender, CoreWebView2NewWindowRequestedEventArgs e)
    {
        e.Handled = true;
        if (!Uri.TryCreate(e.Uri, UriKind.Absolute, out var url)) return;
        if (SameSite(url)) sender.Navigate(url.AbsoluteUri);
        else if (url.Scheme is "http" or "https" or "mailto") _ = Launcher.LaunchUriAsync(url);
    }

    async void OnNavigationCompleted(CoreWebView2 sender, CoreWebView2NavigationCompletedEventArgs e)
    {
        if (e.IsSuccess) { PageLoaded = true; return; }
        if (e.WebErrorStatus is CoreWebView2WebErrorStatus.OperationCanceled or CoreWebView2WebErrorStatus.ConnectionAborted) return;
        if (App.Options.SelfTest != null) return;
        var dialog = new ContentDialog
        {
            Title = $"Can’t reach {home?.Host ?? "the server"}",
            PrimaryButtonText = "Try again", SecondaryButtonText = "Server…", CloseButtonText = "Cancel",
            DefaultButton = ContentDialogButton.Primary, XamlRoot = Root.XamlRoot,
        };
        var r = await dialog.ShowAsync();
        if (r == ContentDialogResult.Primary && home != null) Load(home);
        else if (r == ContentDialogResult.Secondary && await AskServerAsync(false) is { } u) Load(u);
    }

    /// <summary>Export and Backup: Windows' own Save dialog.</summary>
    async void OnDownloadStarting(CoreWebView2 sender, CoreWebView2DownloadStartingEventArgs e)
    {
        var deferral = e.GetDeferral();
        try
        {
            var name = Path.GetFileName(e.ResultFilePath);
            var ext = Path.GetExtension(name);
            var picker = new FileSavePicker { SuggestedFileName = Path.GetFileNameWithoutExtension(name) };
            InitializeWithWindow.Initialize(picker, Handle);
            picker.FileTypeChoices.Add(ext.Length > 1 ? ext[1..].ToUpperInvariant() : "File", [ext.Length > 0 ? ext : ".txt"]);
            var file = await picker.PickSaveFileAsync();
            if (file == null) { e.Cancel = true; return; }
            var path = file.Path;
            await file.DeleteAsync();                 // the dialog made an empty one; the download takes its place
            e.ResultFilePath = path;
            e.Handled = true;
        }
        catch (Exception x) { Log.Write($"download: {x.Message}"); }
        finally { deferral.Complete(); }
    }

    /// <summary>The page's messages (shell() in app.js): its colours, a reply in, and window requests.</summary>
    void OnMessage(CoreWebView2 sender, CoreWebView2WebMessageReceivedEventArgs e)
    {
        if (!Uri.TryCreate(e.Source, UriKind.Absolute, out var source) || !SameSite(source)) return;
        JsonObject? m;
        try { m = JsonNode.Parse(e.WebMessageAsJson) as JsonObject; }
        catch (Exception) { return; }
        switch (m?["kind"]?.GetValue<string>())
        {
            case "look":
                Root.RequestedTheme = m["dark"]?.GetValue<bool>() == false ? ElementTheme.Light : ElementTheme.Dark;
                break;
            case "replied":
                if (GetForegroundWindow() != Handle) Flash();
                break;
            case "window":
                switch (m["what"]?.GetValue<string>())
                {
                    case "close": Close(); break;
                    case "fullScreen": ToggleFullScreen(); break;
                }
                break;
        }
    }

    public async Task<string> Js(string code) =>
        web?.CoreWebView2 is { } core ? await core.ExecuteScriptAsync(code) : "null";

    async Task<Uri?> AskServerAsync(bool firstRun)
    {
        var box = new TextBox { PlaceholderText = "https://", Text = Settings.Typed ?? App.BuiltInServer, MinWidth = 340 };
        var dialog = new ContentDialog
        {
            Title = "Server", Content = box, PrimaryButtonText = "Open", CloseButtonText = firstRun ? "Quit" : "Cancel",
            DefaultButton = ContentDialogButton.Primary, XamlRoot = Root.XamlRoot,
        };
        while (true)
        {
            if (await dialog.ShowAsync() != ContentDialogResult.Primary) return null;
            if (Settings.Clean(box.Text) is { } u) { Settings.Server = u; return u; }
        }
    }

    void Problem(string title, string text)
    {
        var panel = new StackPanel { Spacing = 12, Margin = new Thickness(48), MaxWidth = 560, VerticalAlignment = VerticalAlignment.Center };
        panel.Children.Add(new TextBlock { Text = title, Style = (Style)Application.Current.Resources["SubtitleTextBlockStyle"], TextWrapping = TextWrapping.Wrap });
        panel.Children.Add(new TextBlock { Text = text, TextWrapping = TextWrapping.Wrap, IsTextSelectionEnabled = true });
        Grid.SetRow(panel, 1);
        Root.Children.Add(panel);
    }

    // ---- pictures, for the self-test ------------------------------------------------------

    public async Task Shot(string path)
    {
        if (web?.CoreWebView2 is not { } core) return;
        using var stream = new InMemoryRandomAccessStream();
        await core.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, stream);
        await File.WriteAllBytesAsync(path, await Bytes(stream));
    }

    /// <summary>The title bar and its menus (the web view isn't drawn by XAML, so it's the row alone).</summary>
    public async Task TitleShot(string path)
    {
        var rtb = new RenderTargetBitmap();
        await rtb.RenderAsync(TitleRow);
        var pixels = await rtb.GetPixelsAsync();
        using var stream = new InMemoryRandomAccessStream();
        var encoder = await BitmapEncoder.CreateAsync(BitmapEncoder.PngEncoderId, stream);
        encoder.SetPixelData(BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied, (uint)rtb.PixelWidth, (uint)rtb.PixelHeight, 96, 96, pixels.ToArray());
        await encoder.FlushAsync();
        await File.WriteAllBytesAsync(path, await Bytes(stream));
    }

    static async Task<byte[]> Bytes(IRandomAccessStream stream)
    {
        var bytes = new byte[stream.Size];
        using var reader = new DataReader(stream.GetInputStreamAt(0));
        await reader.LoadAsync((uint)stream.Size);
        reader.ReadBytes(bytes);
        return bytes;
    }

    // ---- Win32 -------------------------------------------------------------------------

    /// <summary>A reply came in while she was in another window: the taskbar button flashes until she comes back.</summary>
    void Flash()
    {
        var info = new FLASHWINFO { cbSize = (uint)Marshal.SizeOf<FLASHWINFO>(), hwnd = Handle, dwFlags = 2 | 12, uCount = 0, dwTimeout = 0 };
        FlashWindowEx(ref info);
    }

    [StructLayout(LayoutKind.Sequential)]
    struct FLASHWINFO { public uint cbSize; public IntPtr hwnd; public uint dwFlags; public uint uCount; public uint dwTimeout; }

    [DllImport("user32.dll")] static extern bool FlashWindowEx(ref FLASHWINFO info);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern uint GetDpiForWindow(IntPtr window);
}
