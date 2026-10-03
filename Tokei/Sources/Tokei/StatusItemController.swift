import AppKit
import os

/// 菜单栏入口的生命周期。系统重建显示环境后重新注册入口，不重启用量采集器。
final class StatusItemController {
    private(set) var item: NSStatusItem
    private weak var target: AnyObject?
    private let action: Selector
    private let canRebuild: () -> Bool
    private let didRebuild: () -> Void
    private var observers: [(NotificationCenter, NSObjectProtocol)] = []
    private var recoveryWork: DispatchWorkItem?
    private var pendingReason: String?
    private let logger = Logger(subsystem: "com.tokei.app", category: "StatusItem")

    init(target: AnyObject, action: Selector, canRebuild: @escaping () -> Bool,
         didRebuild: @escaping () -> Void) {
        self.target = target
        self.action = action
        self.canRebuild = canRebuild
        self.didRebuild = didRebuild
        item = Self.makeItem(target: target, action: action)

        observe(NSWorkspace.didWakeNotification, center: NSWorkspace.shared.notificationCenter)
        observe(NSWorkspace.screensDidWakeNotification, center: NSWorkspace.shared.notificationCenter)
        observe(NSApplication.didChangeScreenParametersNotification, center: .default)
    }

    deinit {
        recoveryWork?.cancel()
        for (center, token) in observers { center.removeObserver(token) }
        NSStatusBar.system.removeStatusItem(item)
    }

    private static func makeItem(target: AnyObject?, action: Selector) -> NSStatusItem {
        // 保留 macOS 26 的正方形占位处理，内容准备好后再定宽（issue #8）。
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        item.isVisible = true
        item.button?.target = target
        item.button?.action = action
        item.button?.sendAction(on: [.leftMouseUp, .rightMouseUp])
        return item
    }

    private func observe(_ name: Notification.Name, center: NotificationCenter) {
        let token = center.addObserver(forName: name, object: nil, queue: .main) { [weak self] _ in
            self?.scheduleRecovery(reason: name.rawValue)
        }
        observers.append((center, token))
    }

    /// 唤醒与屏幕变化常连续到达；等布局稳定一秒再重建，只处理最后一次通知。
    private func scheduleRecovery(reason: String) {
        recoveryWork?.cancel()
        pendingReason = reason
        let work = DispatchWorkItem { [weak self] in self?.recoverPending() }
        recoveryWork = work
        DispatchQueue.main.asyncAfter(deadline: .now() + 1, execute: work)
    }

    /// 面板关闭后继续先前延后的恢复，不移除用户正在操作的弹窗锚点。
    func resumeRecovery() {
        guard let reason = pendingReason else { return }
        scheduleRecovery(reason: reason)
    }

    /// 重新打开应用也是显式恢复入口；不能只给失效的旧项目重复赋 isVisible。
    func recoverOnReopen() {
        recoveryWork?.cancel()
        pendingReason = "reopen"
        recoverPending()
    }

    private func recoverPending() {
        recoveryWork = nil
        guard let reason = pendingReason, canRebuild() else { return }
        pendingReason = nil
        let name = item.autosaveName
        // isVisible 为 true 也可能被遮挡；它不能作为系统托管视图是否健康的判断。
        // 移除并新建真正重新注册入口，保持原来的持久化标识与左右键行为。
        NSStatusBar.system.removeStatusItem(item)
        item = Self.makeItem(target: target, action: action)
        item.autosaveName = name
        item.isVisible = true
        didRebuild()
        logger.notice("Recreated menu bar item: \(reason, privacy: .public), width=\(self.item.length)")
    }
}
