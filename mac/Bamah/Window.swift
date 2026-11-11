import AppKit
import UserNotifications
import WebKit

/// One window on her Bamah. The page is all of it; the window adds the Mac's Save and Open panels,
/// sends other sites' links to the browser, and colours its title bar like the page's side list.
@MainActor
final class WindowController: NSWindowController, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate,
                              WKScriptMessageHandler, WKDownloadDelegate {
    static var all: [WindowController] = []
    static let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"

    let web: WKWebView
    private(set) var home: URL
    private(set) var loaded = false
    private var titleWatch: NSKeyValueObservation?

    static func open(_ url: URL) {
        let c = WindowController(url)
        if let last = all.last?.window, let w = c.window {
            w.setFrameTopLeftPoint(w.cascadeTopLeft(from: NSPoint(x: last.frame.minX, y: last.frame.maxY)))
        }
        all.append(c)
        c.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    init(_ url: URL) {
        home = url
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()              // the sign-in is kept, as in a browser
        config.applicationNameForUserAgent = "Version/26.0 Safari/605.1.15 BamahApp/\(Self.version)"
        config.preferences.isElementFullscreenEnabled = true
        web = WKWebView(frame: .zero, configuration: config)
        web.allowsMagnification = false
        web.setValue(false, forKey: "drawsBackground")     // the window's colour shows until the page paints

        let w = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1280, height: 820),
                         styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        w.title = "Bamah"
        w.titleVisibility = .hidden
        w.titlebarAppearsTransparent = true
        w.tabbingMode = .disallowed
        w.minSize = NSSize(width: 800, height: 560)
        w.contentView = web
        super.init(window: w)
        paint(NSColor(red: 0x17 / 255, green: 0x12 / 255, blue: 0x13 / 255, alpha: 1), dark: true)
        if Self.all.isEmpty {
            if !w.setFrameUsingName("Bamah") { w.center() }
            w.setFrameAutosaveName("Bamah")
        }
        w.delegate = self
        web.navigationDelegate = self
        web.uiDelegate = self
        config.userContentController.add(Relay(self), name: "bamah")
        titleWatch = web.observe(\.title) { [weak self] web, _ in
            MainActor.assumeIsolated { self?.window?.title = (web.title ?? "").isEmpty ? "Bamah" : web.title! }
        }
        load(url)
    }

    required init?(coder: NSCoder) { fatalError("not from a nib") }

    func load(_ url: URL) {
        home = url
        loaded = false
        web.load(URLRequest(url: url))
    }

    func command(_ name: String) {
        let arg = (try? String(data: JSONSerialization.data(withJSONObject: [name]), encoding: .utf8)) ?? "[]"
        web.evaluateJavaScript("window.bamahCommand && window.bamahCommand(...\(arg))", completionHandler: nil)
    }

    func windowWillClose(_ note: Notification) {
        web.configuration.userContentController.removeScriptMessageHandler(forName: "bamah")
        Self.all.removeAll { $0 === self }
    }

    /// The title bar takes the colour of the page's side list, light or dark as the theme is.
    private func paint(_ color: NSColor, dark: Bool) {
        window?.backgroundColor = color
        window?.appearance = NSAppearance(named: dark ? .darkAqua : .aqua)
    }

    private func sameSite(_ url: URL) -> Bool {
        url.host?.lowercased() == home.host?.lowercased() && url.port == home.port
    }

    // MARK: the page's messages (shell() in app.js)

    func received(_ body: Any) {
        guard let m = body as? [String: Any], let kind = m["kind"] as? String else { return }
        switch kind {
        case "look":
            if let rgb = m["bar"] as? String, let color = Self.color(rgb) { paint(color, dark: (m["dark"] as? Bool) ?? true) }
        case "replied":
            Ping.replied(name: m["name"] as? String ?? "", scene: m["scene"] as? String ?? "")
        default:
            break
        }
    }

    /// "rgb(23, 18, 19)" → a colour.
    static func color(_ css: String) -> NSColor? {
        let n = css.split(whereSeparator: { !"0123456789.".contains($0) }).compactMap { Double($0) }
        guard n.count >= 3 else { return nil }
        return NSColor(srgbRed: n[0] / 255, green: n[1] / 255, blue: n[2] / 255, alpha: 1)
    }

    // MARK: navigation: her Bamah stays here; another site's link opens in the browser

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping @MainActor (WKNavigationActionPolicy) -> Void) {
        if action.shouldPerformDownload { return decisionHandler(.download) }
        guard let url = action.request.url, let scheme = url.scheme?.lowercased() else { return decisionHandler(.cancel) }
        if ["about", "blob", "data"].contains(scheme) || sameSite(url) { return decisionHandler(.allow) }
        if action.navigationType == .linkActivated || action.targetFrame == nil {
            if ["http", "https", "mailto"].contains(scheme) { NSWorkspace.shared.open(url) }
            return decisionHandler(.cancel)
        }
        decisionHandler(.allow)        // a redirect, like a sign-in page in front of the server
    }

    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse,
                 decisionHandler: @escaping @MainActor (WKNavigationResponsePolicy) -> Void) {
        let disposition = (response.response as? HTTPURLResponse)?.value(forHTTPHeaderField: "Content-Disposition") ?? ""
        decisionHandler(disposition.lowercased().hasPrefix("attachment") || !response.canShowMIMEType ? .download : .allow)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) { loaded = true }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        let e = error as NSError
        if e.code == NSURLErrorCancelled || e.code == 102 { return }       // 102: handed to a download
        let alert = NSAlert()
        alert.messageText = "Can’t reach \(home.host ?? "the server")"
        alert.informativeText = e.localizedDescription
        alert.addButton(withTitle: "Try Again")
        alert.addButton(withTitle: "Server…")
        alert.addButton(withTitle: "Cancel")
        guard let w = window else { return }
        alert.beginSheetModal(for: w) { r in
            if r == .alertFirstButtonReturn { self.load(self.home) }
            else if r == .alertSecondButtonReturn { (NSApp.delegate as? BamahApp)?.changeServer(nil) }
        }
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) { webView.reload() }

    // window.open and target=_blank: the browser
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url, sameSite(url) { webView.load(action.request) }
        else if let url = action.request.url { NSWorkspace.shared.open(url) }
        return nil
    }

    // MARK: the Mac's own panels

    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping @MainActor ([URL]?) -> Void) {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.canChooseDirectories = false
        guard let w = window else { return completionHandler(nil) }
        panel.beginSheetModal(for: w) { r in completionHandler(r == .OK ? panel.urls : nil) }
    }

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping @MainActor () -> Void) {
        let alert = NSAlert()
        alert.messageText = message
        guard let w = window else { return completionHandler() }
        alert.beginSheetModal(for: w) { _ in completionHandler() }
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping @MainActor (Bool) -> Void) {
        let alert = NSAlert()
        alert.messageText = message
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Cancel")
        guard let w = window else { return completionHandler(false) }
        alert.beginSheetModal(for: w) { r in completionHandler(r == .alertFirstButtonReturn) }
    }

    // MARK: Export and Backup: a Save panel

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { download.delegate = self }
    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) { download.delegate = self }

    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String,
                  completionHandler: @escaping @MainActor (URL?) -> Void) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = suggestedFilename
        guard let w = window else { return completionHandler(nil) }
        panel.beginSheetModal(for: w) { r in
            guard r == .OK, let url = panel.url else { return completionHandler(nil) }
            try? FileManager.default.removeItem(at: url)      // the panel has already asked about replacing it
            completionHandler(url)
        }
    }

    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        guard let w = window else { return }
        let alert = NSAlert(error: error)
        alert.beginSheetModal(for: w)
    }

    // the WKScriptMessageHandler requirement; Relay forwards here without keeping the window alive
    func userContentController(_ c: WKUserContentController, didReceive message: WKScriptMessage) { received(message.body) }
}

/// The user content controller keeps its handlers; this one holds the window weakly, so closing it frees it.
@MainActor
final class Relay: NSObject, WKScriptMessageHandler {
    weak var to: WindowController?
    init(_ to: WindowController) { self.to = to }
    func userContentController(_ c: WKUserContentController, didReceive message: WKScriptMessage) { to?.received(message.body) }
}

/// A reply came in while she was in another app: the Dock icon bounces once, and a notification says who.
@MainActor
enum Ping {
    static func replied(name: String, scene: String) {
        guard !NSApp.isActive else { return }
        NSApp.requestUserAttention(.informationalRequest)
        let c = UNMutableNotificationContent()
        c.title = name.isEmpty ? "Bamah" : name
        c.body = scene
        c.sound = .default
        UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: UUID().uuidString, content: c, trigger: nil))
    }
}
