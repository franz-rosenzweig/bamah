#if SELFTEST
import AppKit
import WebKit

/// Drives the app from inside on a test server (selftest.sh): the page loads in the app, the menu
/// bar's items reach the page, and pictures of what the window shows land in -BamahSelfTest.
@MainActor
enum SelfTest {
    static var lines: [String] = []
    static var failed = 0

    static func start() {
        guard let out = UserDefaults.standard.string(forKey: "BamahSelfTest") else { return }
        let dir = URL(fileURLWithPath: out)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        Task { @MainActor in
            await run(dir)
            try? lines.joined(separator: "\n").write(to: dir.appendingPathComponent("log.txt"), atomically: true, encoding: .utf8)
            NSApp.terminate(nil)
        }
    }

    static func check(_ ok: Bool, _ what: String) {
        if !ok { failed += 1 }
        lines.append((ok ? "ok    " : "FAIL  ") + what)
    }

    static func wait(_ seconds: Double) async { try? await Task.sleep(nanoseconds: UInt64(seconds * 1e9)) }

    static func js(_ w: WindowController, _ code: String) async -> Any? {
        try? await w.web.evaluateJavaScript(code)
    }

    static func shot(_ w: WindowController, _ dir: URL, _ name: String) async {
        guard let image = try? await w.web.takeSnapshot(configuration: nil),
              let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
              let png = rep.representation(using: .png, properties: [:]) else { return check(false, "picture \(name)") }
        try? png.write(to: dir.appendingPathComponent("\(name).png"))
    }

    /// The menu item that runs this page command, as a click on it would.
    static func menu(_ command: String) -> Bool {
        func find(_ m: NSMenu?) -> NSMenuItem? {
            for it in m?.items ?? [] {
                if it.representedObject as? String == command { return it }
                if let f = find(it.submenu) { return f }
            }
            return nil
        }
        guard let it = find(NSApp.mainMenu), let menu = it.menu else { return false }
        menu.performActionForItem(at: menu.index(of: it))
        return true
    }

    static func run(_ dir: URL) async {
        for _ in 0..<150 where !(WindowController.all.first?.loaded ?? false) { await wait(0.1) }
        guard let w = WindowController.all.first, w.loaded else { return check(false, "the page loads") }
        check(true, "the page loads from \(w.home.absoluteString)")
        w.window?.setContentSize(NSSize(width: 1280, height: 820))
        if let start = UserDefaults.standard.string(forKey: "BamahStart") { _ = await js(w, "location.hash = \(String(reflecting: start))") }
        await wait(2.5)
        let ua = await js(w, "navigator.userAgent") as? String ?? ""
        check(ua.contains("BamahApp/"), "the page knows it's in the app")
        check(await js(w, "typeof window.bamahCommand") as? String == "function", "the page takes commands")
        let titles = NSApp.mainMenu?.items.map(\.title) ?? []
        check(titles == ["Bamah", "File", "Edit", "Scene", "View", "Window", "Help"], "menus: \(titles.joined(separator: ", "))")
        await shot(w, dir, "scene")

        check(menu("journal"), "View › Journal is there")
        await wait(0.8)
        check(await js(w, "localStorage.getItem('bamah.side')") as? String == "journal", "View › Journal opens the journal")
        await shot(w, dir, "journal")

        _ = menu("bigger")
        await wait(0.3)
        check(await js(w, "localStorage.getItem('bamah.size')") as? String == "1.12", "View › Bigger")
        _ = menu("actualSize")
        await wait(0.3)
        check(await js(w, "localStorage.getItem('bamah.size')") as? String == "1", "View › Actual Size")

        _ = menu("settings")
        await wait(1.2)
        check(await js(w, "location.hash") as? String == "#/settings", "Bamah › Settings…")
        await shot(w, dir, "settings")

        let bar = w.window?.backgroundColor.usingColorSpace(.sRGB)
        check(bar != nil && (bar!.redComponent < 0.2), "the title bar takes the page's colour")
        lines.append(failed == 0 ? "PASSED" : "FAILED \(failed)")
    }
}
#endif
