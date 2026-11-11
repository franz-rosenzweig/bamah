import AppKit
import UserNotifications

/// Bamah for the Mac: a window around the Bamah she already uses, with a menu bar, the Mac's own
/// Save and Open panels, and a ping when a reply comes in while she's in another app. The page
/// itself is the whole interface; nothing of hers is kept in the app (README.md).
@main
@MainActor
final class BamahApp: NSObject, NSApplicationDelegate {
    private static var strong: BamahApp?      // NSApplication holds its delegate weakly

    static func main() {
        let app = NSApplication.shared
        strong = BamahApp()
        app.delegate = strong
        app.run()
    }

    func applicationDidFinishLaunching(_ note: Notification) {
        NSApp.mainMenu = Menus.make()
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
        if let url = Server.url {
            WindowController.open(url)
        } else if let url = Server.ask(firstRun: true) {
            WindowController.open(url)
        } else {
            NSApp.terminate(nil)
        }
        #if SELFTEST
        SelfTest.start()
        #endif
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows: Bool) -> Bool {
        if !hasVisibleWindows, let url = Server.url { WindowController.open(url) }
        return true
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }

    // The menu bar's own items (Menus.swift); the scene's go to the page.

    @objc func newWindow(_ sender: Any?) {
        if let url = Server.url { WindowController.open(url) }
    }

    @objc func changeServer(_ sender: Any?) {
        guard let url = Server.ask(firstRun: false) else { return }
        WindowController.all.forEach { $0.load(url) }
        if WindowController.all.isEmpty { WindowController.open(url) }
    }

    @objc func help(_ sender: Any?) {
        NSWorkspace.shared.open(URL(string: "https://docs.tiresia.xyz/bamah/")!)
    }

    /// A menu item whose representedObject names one of the page's commands (window.bamahCommand).
    @objc func command(_ sender: NSMenuItem) {
        guard let name = sender.representedObject as? String else { return }
        let target = (NSApp.keyWindow?.windowController as? WindowController) ?? WindowController.all.first
        target?.command(name)
    }
}
