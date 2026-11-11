import AppKit

/// The menu bar. Bamah's own items call the page's commands (window.bamahCommand in app.js), so a
/// key does the same thing as the button it stands for. The page leaves these keys alone on a Mac.
@MainActor
enum Menus {
    static func make() -> NSMenu {
        let bar = NSMenu()
        let app = NSApp.delegate as? BamahApp

        bar.addItem(sub("Bamah", [
            item("About Bamah", #selector(NSApplication.orderFrontStandardAboutPanel(_:)), target: NSApp),
            .separator(),
            page("Settings…", "settings", ","),
            item("Server…", #selector(BamahApp.changeServer(_:)), target: app),
            .separator(),
            item("Hide Bamah", #selector(NSApplication.hide(_:)), "h", target: NSApp),
            item("Hide Others", #selector(NSApplication.hideOtherApplications(_:)), "h", [.command, .option], target: NSApp),
            item("Show All", #selector(NSApplication.unhideAllApplications(_:)), target: NSApp),
            .separator(),
            item("Quit Bamah", #selector(NSApplication.terminate(_:)), "q", target: NSApp),
        ]))

        bar.addItem(sub("File", [
            page("New Story", "newStory", "n"),
            page("New Scene", "newScene", "n", [.command, .shift]),
            page("New Character", "newCharacter"),
            .separator(),
            item("New Window", #selector(BamahApp.newWindow(_:)), "n", [.command, .option], target: app),
            item("Close", #selector(NSWindow.performClose(_:)), "w"),
        ]))

        // The responder chain finds the web view for these, and macOS adds Dictation and Emoji itself.
        bar.addItem(sub("Edit", [
            item("Undo", Selector(("undo:")), "z"),
            item("Redo", Selector(("redo:")), "z", [.command, .shift]),
            .separator(),
            item("Cut", #selector(NSText.cut(_:)), "x"),
            item("Copy", #selector(NSText.copy(_:)), "c"),
            item("Paste", #selector(NSText.paste(_:)), "v"),
            item("Select All", #selector(NSText.selectAll(_:)), "a"),
            .separator(),
            sub("Spelling and Grammar", [
                item("Show Spelling and Grammar", #selector(NSText.showGuessPanel(_:)), ":"),
                item("Check Document Now", #selector(NSText.checkSpelling(_:)), ";"),
                .separator(),
                item("Check Spelling While Typing", #selector(NSTextView.toggleContinuousSpellChecking(_:))),
                item("Check Grammar With Spelling", #selector(NSTextView.toggleGrammarChecking(_:))),
            ]),
        ]))

        bar.addItem(sub("Scene", [
            page("Send", "next", "\r"),
            page("Go On", "goOn", "]"),
            page("Again", "again", "r"),
            page("Write My Line", "writeMyLine", "l"),
            page("Stop", "stop", "."),
            .separator(),
            page("What If…", "whatIf", "w", [.command, .shift]),
        ]))

        let bigger = page("Bigger", "bigger", "+")
        let biggerToo = page("Bigger", "bigger", "=")      // ⌘= without the Shift, as in Safari
        biggerToo.isHidden = true
        biggerToo.allowsKeyEquivalentWhenHidden = true
        bar.addItem(sub("View", [
            page("Feelings", "feelings", "1"),
            page("Memory", "memory", "2"),
            page("Journal", "journal", "3"),
            .separator(),
            bigger, biggerToo,
            page("Smaller", "smaller", "-"),
            page("Actual Size", "actualSize", "0"),
            .separator(),
            item("Enter Full Screen", #selector(NSWindow.toggleFullScreen(_:)), "f", [.command, .control]),
        ]))

        let window = sub("Window", [
            item("Minimize", #selector(NSWindow.performMiniaturize(_:)), "m"),
            item("Zoom", #selector(NSWindow.performZoom(_:))),
            .separator(),
            item("Bring All to Front", #selector(NSApplication.arrangeInFront(_:)), target: NSApp),
        ])
        bar.addItem(window)
        NSApp.windowsMenu = window.submenu

        let help = sub("Help", [item("Bamah Help", #selector(BamahApp.help(_:)), "?", target: app)])
        bar.addItem(help)
        NSApp.helpMenu = help.submenu
        return bar
    }

    static func sub(_ title: String, _ items: [NSMenuItem]) -> NSMenuItem {
        let menu = NSMenu(title: title)
        items.forEach(menu.addItem)
        let top = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        top.submenu = menu
        return top
    }

    static func item(_ title: String, _ action: Selector, _ key: String = "", _ mods: NSEvent.ModifierFlags = .command,
                     target: AnyObject? = nil) -> NSMenuItem {
        let it = NSMenuItem(title: title, action: action, keyEquivalent: key)
        it.keyEquivalentModifierMask = mods
        it.target = target
        return it
    }

    /// An item that runs one of the page's commands.
    static func page(_ title: String, _ command: String, _ key: String = "", _ mods: NSEvent.ModifierFlags = .command) -> NSMenuItem {
        let it = item(title, #selector(BamahApp.command(_:)), key, mods, target: NSApp.delegate as? BamahApp)
        it.representedObject = command
        return it
    }
}
