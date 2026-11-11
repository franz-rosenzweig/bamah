import AppKit

/// Which Bamah the app opens: the address she typed, kept in the app's settings, or the one this
/// build was given (build.sh: BAMAH_DEFAULT_SERVER or local.env), offered the first time.
@MainActor
enum Server {
    private static let key = "BamahServer"

    static var url: URL? {
        if let given = UserDefaults.standard.string(forKey: "BamahServerOnce"), let u = clean(given) { return u }  // a test run
        return UserDefaults.standard.string(forKey: key).flatMap(clean)
    }

    static var builtIn: String {
        (Bundle.main.object(forInfoDictionaryKey: "BamahDefaultServer") as? String ?? "").trimmingCharacters(in: .whitespaces)
    }

    /// "bamah.example.com" or "http://192.168.1.5:8465/" → a URL with a scheme and no trailing slash.
    static func clean(_ text: String) -> URL? {
        var s = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if s.isEmpty { return nil }
        if !s.contains("://") { s = "https://" + s }
        while s.hasSuffix("/") { s.removeLast() }
        guard let u = URL(string: s), let scheme = u.scheme?.lowercased(), ["http", "https"].contains(scheme), u.host != nil else { return nil }
        return u
    }

    /// Asks for the address. Nil when she cancels (or quits, the first time).
    static func ask(firstRun: Bool) -> URL? {
        let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 320, height: 24))
        field.placeholderString = "https://"
        field.stringValue = UserDefaults.standard.string(forKey: key) ?? builtIn
        let alert = NSAlert()
        alert.messageText = "Server"
        alert.accessoryView = field
        alert.addButton(withTitle: "Open")
        alert.addButton(withTitle: firstRun ? "Quit" : "Cancel")
        alert.window.initialFirstResponder = field
        while true {
            NSApp.activate(ignoringOtherApps: true)
            guard alert.runModal() == .alertFirstButtonReturn else { return nil }
            if let u = clean(field.stringValue) {
                UserDefaults.standard.set(u.absoluteString, forKey: key)
                return u
            }
            NSSound.beep()
        }
    }
}
