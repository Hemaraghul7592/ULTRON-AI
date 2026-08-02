import SwiftUI

public struct MarketSidebar: View {
    @Binding var searchQuery: String
    let favorites: Set<String>
    let recentSymbols: [String]
    let selectedSymbol: String?
    let onSearch: () -> Void
    let onSelect: (String) -> Void

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                MarketSearchBar(query: $searchQuery, onSubmit: onSearch)
                marketSection("FAVORITES", symbols: Array(favorites).sorted())
                marketSection("RECENT", symbols: recentSymbols)
            }
            .padding(16)
        }
        .frame(width: 220)
        .background(Color.white.opacity(0.025))
        .accessibilityIdentifier("market.sidebar")
    }

    @ViewBuilder
    private func marketSection(_ title: String, symbols: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 10, weight: .bold))
                .tracking(1.2)
                .foregroundStyle(.tertiary)
            if symbols.isEmpty {
                Text("None yet")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(symbols, id: \.self) { symbol in
                    Button {
                        onSelect(symbol)
                    } label: {
                        HStack(spacing: 9) {
                            Image(systemName: symbol == selectedSymbol ? "chart.line.uptrend.xyaxis.circle.fill" : "chart.line.uptrend.xyaxis.circle")
                                .foregroundStyle(symbol == selectedSymbol ? .blue : .secondary)
                            Text(symbol)
                            Spacer()
                        }
                        .font(.subheadline.weight(symbol == selectedSymbol ? .semibold : .regular))
                        .foregroundStyle(.primary)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 7)
                        .background(symbol == selectedSymbol ? .blue.opacity(0.13) : .clear, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
                    }
                    .buttonStyle(.plain)
                    .contextMenu { Button("Open \(symbol)") { onSelect(symbol) } }
                    .accessibilityLabel("Open market symbol \(symbol)")
                }
            }
        }
    }
}
