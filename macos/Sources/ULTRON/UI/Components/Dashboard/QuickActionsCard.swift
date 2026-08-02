import SwiftUI

public struct QuickActionsCard: View {
    private let state: DashboardCardState
    private let onRefresh: () -> Void

    public init(state: DashboardCardState, onRefresh: @escaping () -> Void) {
        self.state = state
        self.onRefresh = onRefresh
    }

    public var body: some View {
        DashboardCard(title: "Quick Actions", subtitle: "Move through your workflow", icon: "bolt.fill", tint: .yellow, state: state) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Refresh connected providers and update every dashboard card.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                actionButton("Refresh data", icon: "arrow.clockwise", action: onRefresh)
                    .frame(maxWidth: 180)
            }
        }
    }

    private func actionButton(_ title: String, icon: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Label(title, systemImage: icon)
                .font(.caption.weight(.medium))
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.bordered)
        .controlSize(.small)
        .help(title)
        .accessibilityLabel(title)
    }
}
