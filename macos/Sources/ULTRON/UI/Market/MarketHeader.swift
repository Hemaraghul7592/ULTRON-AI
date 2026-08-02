import SwiftUI

public struct MarketHeader: View {
    let company: CompanyProfile?
    let quote: Quote?
    let lastUpdated: Date?
    let isRefreshing: Bool
    let isFavorite: Bool
    let onRefresh: () -> Void
    let onFavorite: () -> Void

    public var body: some View {
        HStack(alignment: .top, spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 10) {
                    Text(company?.symbol ?? "Market")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                    Button(action: onFavorite) {
                        Image(systemName: isFavorite ? "star.fill" : "star")
                            .foregroundStyle(isFavorite ? .yellow : .secondary)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(isFavorite ? "Remove from favorites" : "Add to favorites")
                }
                Text(company?.name ?? "Search for a company or symbol")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 5) {
                Text(quote?.price.formatted(.currency(code: quote?.currency ?? "USD")) ?? "Unavailable")
                    .font(.title2.weight(.semibold))
                Text(quote.map { "\($0.change >= 0 ? "+" : "")\($0.change.formatted(.number)) (\($0.changePercent.formatted(.percent)))" } ?? "Price unavailable")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(quote.map { $0.change >= 0 ? Color.green : Color.red } ?? .secondary)
            }
            if let lastUpdated {
                Text(lastUpdated.formatted(date: .omitted, time: .shortened))
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
            Button(action: onRefresh) {
                Image(systemName: "arrow.clockwise")
                    .rotationEffect(.degrees(isRefreshing ? 360 : 0))
                    .animation(isRefreshing ? .linear(duration: 1).repeatForever(autoreverses: false) : .default, value: isRefreshing)
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
            .disabled(isRefreshing)
            .accessibilityLabel("Refresh market data")
        }
        .accessibilityIdentifier("market.header")
    }
}
