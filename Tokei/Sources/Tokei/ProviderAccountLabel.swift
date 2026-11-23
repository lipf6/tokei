import SwiftUI

struct ProviderAccountLabel: View {
    let account: String
    @State private var revealed = false

    static func masked(_ account: String) -> String {
        guard !account.isEmpty else { return "" }
        let separator = account.lastIndex(of: "@").flatMap {
            $0 != account.startIndex && account.index(after: $0) != account.endIndex ? $0 : nil
        } ?? account.endIndex
        let name = account[..<separator]
        let domain = account[separator...]
        let count = name.count
        let visible = count >= 7 ? 2 : 1
        let first = count >= 2 ? String(name.prefix(visible)) : ""
        let last = count >= 3 ? String(name.suffix(visible)) : ""
        return first + "•••" + last + domain
    }

    var body: some View {
        let action = revealed ? L("隐藏账号") : L("显示账号")
        let displayed = revealed ? account : Self.masked(account)
        Button {
            revealed.toggle()
        } label: {
            HStack(spacing: 4) {
                Text(verbatim: displayed)
                    .fixedSize(horizontal: false, vertical: true)
                Image(systemName: revealed ? "eye.slash" : "eye")
            }
            .font(.system(size: Theme.fontSize(9), design: .monospaced))
            .foregroundStyle(Theme.tSecondary)
            .padding(.vertical, 2)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .help(action)
        .accessibilityLabel(Text(action))
        .accessibilityValue(Text(verbatim: displayed))
        .onReceive(NotificationCenter.default.publisher(for: NSPopover.didCloseNotification)) { _ in
            revealed = false
        }
    }
}
