import SwiftUI

public struct WatchlistCard: View {
    private let watchlists: [Watchlist]
    private let state: DashboardCardState

    public init(watchlists: [Watchlist], state: DashboardCardState) {
        self.watchlists = watchlists
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "Watchlist", subtitle: "Symbols you are tracking", icon: "eye.fill", tint: .orange, state: state) {
            VStack(alignment: .leading, spacing: 12) {
                ForEach(watchlists.prefix(3)) { watchlist in
                    HStack {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(watchlist.name)
                                .font(.subheadline.weight(.semibold))
                            Text(watchlist.symbols.prefix(4).map(\.symbol).joined(separator: "  "))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                        }
                        Spacer()
                        Text("\(watchlist.symbols.count)")
                            .font(.caption.weight(.bold))
                            .foregroundStyle(.orange)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 5)
                            .background(.orange.opacity(0.12), in: Capsule())
                    }
                }
            }
        }
    }
}
