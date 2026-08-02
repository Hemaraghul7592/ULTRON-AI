import SwiftUI

public struct PortfolioWorkspaceWatchlistCard: View {
    let watchlists: [Watchlist]
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Watchlists", subtitle: "Tracked symbols", icon: "eye.fill", tint: .yellow, state: state) {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(watchlists.prefix(4)) { watchlist in
                    HStack {
                        Text(watchlist.name).font(.subheadline.weight(.semibold))
                        Spacer()
                        Text("\(watchlist.symbols.count) symbols")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }
}
