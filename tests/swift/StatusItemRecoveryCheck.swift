import AppKit

private final class ClickTarget: NSObject {
    @objc func clicked(_ sender: Any?) {}
}

@main
struct StatusItemRecoveryCheck {
    static func main() {
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.accessory)
        let target = ClickTarget()
        let action = #selector(ClickTarget.clicked(_:))
        var panelOpen = false
        var rebuilt = 0
        weak var current: StatusItemController?
        var controller: StatusItemController? = StatusItemController(
            target: target, action: action,
            canRebuild: { !panelOpen },
            didRebuild: {
                rebuilt += 1
                current?.item.button?.title = "99 · 96"
                current?.item.length = 100
            }
        )
        current = controller
        let first = controller!.item
        let name = first.autosaveName
        // 模拟旧入口被系统移除但应用仍持有对象；重新打开必须创建新的注册。
        NSStatusBar.system.removeStatusItem(first)
        controller!.recoverOnReopen()
        precondition(controller!.item !== first)
        precondition(controller!.item.isVisible)
        precondition(controller!.item.autosaveName == name)
        precondition(controller!.item.button?.target === target)
        precondition(controller!.item.button?.action == action)
        precondition(controller!.item.button?.title == "99 · 96")
        precondition(rebuilt == 1)

        let workspace = NSWorkspace.shared.notificationCenter
        let beforeWake = controller!.item
        workspace.post(name: NSWorkspace.didWakeNotification, object: nil)
        workspace.post(name: NSWorkspace.screensDidWakeNotification, object: nil)
        NotificationCenter.default.post(name: NSApplication.didChangeScreenParametersNotification,
                                        object: nil)
        precondition(controller!.item === beforeWake, "must wait for display layout to settle")
        pump()
        precondition(rebuilt == 2, "a burst of notifications must rebuild only once")
        precondition(controller!.item !== beforeWake)
        precondition(controller!.item.button?.window != nil, "the replacement must have a popover anchor")
        precondition((controller!.item.button?.bounds.width ?? 0) > 0, "the replacement anchor must have a width")

        panelOpen = true
        let anchor = controller!.item
        workspace.post(name: NSWorkspace.screensDidWakeNotification, object: nil)
        pump()
        precondition(controller!.item === anchor, "do not remove a visible popover's anchor")
        panelOpen = false
        controller!.resumeRecovery()
        pump()
        precondition(controller!.item !== anchor)
        precondition(rebuilt == 3)

        workspace.post(name: NSWorkspace.didWakeNotification, object: nil)
        controller!.recoverOnReopen()
        precondition(rebuilt == 4)
        pump()
        precondition(rebuilt == 4, "reopen must cancel any pending automatic recovery")

        workspace.post(name: NSWorkspace.didWakeNotification, object: nil)
        controller = nil
        precondition(current == nil, "notification observers must not retain the controller")
        pump()
        precondition(rebuilt == 4, "teardown must cancel pending recovery")
        print("status item recovery checks passed")
    }

    private static func pump() {
        RunLoop.main.run(until: Date().addingTimeInterval(1.2))
    }
}
