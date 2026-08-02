import SwiftUI

public struct RelatedCompaniesCard: View {
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Related Companies", subtitle: "Comparable company discovery", icon: "person.3.fill", tint: .indigo, state: state) {
            EmptyStateCard(title: "Related company data is unavailable.", icon: "person.3")
        }
    }
}
