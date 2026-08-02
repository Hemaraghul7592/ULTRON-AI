import SwiftUI

public struct AlertCard: View {
    private let alerts: [Alert]
    private let state: DashboardCardState

    public init(alerts: [Alert], state: DashboardCardState) {
        self.alerts = alerts
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "Active Alerts", subtitle: "Requires your attention", icon: "bell.badge.fill", tint: .red, state: state) {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(alerts.prefix(3)) { alert in
                    HStack(alignment: .top, spacing: 10) {
                        Image(systemName: "circle.fill")
                            .font(.system(size: 7))
                            .foregroundStyle(color(for: alert.severity))
                            .padding(.top, 5)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(alert.title)
                                .font(.subheadline.weight(.semibold))
                                .lineLimit(1)
                            Text(alert.message)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(2)
                        }
                    }
                }
            }
        }
    }

    private func color(for severity: AlertSeverity) -> Color {
        switch severity {
        case .critical, .high: .red
        case .medium: .orange
        case .low: .yellow
        case .info: .blue
        }
    }
}
