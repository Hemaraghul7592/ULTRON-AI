import SwiftUI

public struct CompetitorComparisonCard: View {
    let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Competitor Comparison", subtitle: "Provider-supported comparisons", icon: "person.2.fill", tint: .indigo, state: state) { EmptyStateCard(title: "Competitor comparison is unavailable.", icon: "person.2") } }
}
