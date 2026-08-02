import SwiftUI

public struct InvestmentChecklistCard: View {
    let items: [ResearchChecklistItem]; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Investment Checklist", subtitle: "Evidence-based research gates", icon: "checklist", tint: .yellow, state: state) { VStack(spacing: 8) { ForEach(items) { item in HStack { Image(systemName: icon(item.status)).foregroundStyle(color(item.status)); Text(item.title).font(.caption); Spacer(); Text(item.status.rawValue).font(.caption2.weight(.semibold)).foregroundStyle(color(item.status)) } } } } }
    private func icon(_ status: ResearchChecklistStatus) -> String { switch status { case .pass: "checkmark.circle.fill"; case .warning: "exclamationmark.triangle.fill"; case .unavailable: "minus.circle" } }
    private func color(_ status: ResearchChecklistStatus) -> Color { switch status { case .pass: .green; case .warning: .orange; case .unavailable: .secondary } }
}
