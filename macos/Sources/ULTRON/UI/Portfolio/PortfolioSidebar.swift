import SwiftUI

public struct PortfolioSidebar: View {
    let portfolios: [Portfolio]
    let watchlists: [Watchlist]
    let selectedPortfolioID: String?
    let onSelectPortfolio: (String) -> Void

    public init(
        portfolios: [Portfolio],
        watchlists: [Watchlist],
        selectedPortfolioID: String?,
        onSelectPortfolio: @escaping (String) -> Void
    ) {
        self.portfolios = portfolios
        self.watchlists = watchlists
        self.selectedPortfolioID = selectedPortfolioID
        self.onSelectPortfolio = onSelectPortfolio
    }

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                sectionTitle("PORTFOLIOS")
                if portfolios.isEmpty {
                    Text("No portfolios yet")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(portfolios) { portfolio in
                        Button {
                            onSelectPortfolio(portfolio.id)
                        } label: {
                            HStack(spacing: 10) {
                                Image(systemName: portfolio.id == selectedPortfolioID ? "briefcase.fill" : "briefcase")
                                    .foregroundStyle(portfolio.id == selectedPortfolioID ? .blue : .secondary)
                                Text(portfolio.name)
                                    .lineLimit(1)
                                Spacer()
                            }
                            .font(.subheadline.weight(portfolio.id == selectedPortfolioID ? .semibold : .regular))
                            .foregroundStyle(.primary)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 9)
                            .background(portfolio.id == selectedPortfolioID ? .blue.opacity(0.14) : .clear, in: RoundedRectangle(cornerRadius: 9, style: .continuous))
                        }
                        .buttonStyle(.plain)
                        .contextMenu {
                            Button("Select Portfolio") { onSelectPortfolio(portfolio.id) }
                        }
                        .accessibilityLabel("Portfolio \(portfolio.name)")
                        .accessibilityAddTraits(portfolio.id == selectedPortfolioID ? .isSelected : [])
                    }
                }

                sectionTitle("WATCHLISTS")
                if watchlists.isEmpty {
                    Text("No watchlists yet")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(watchlists) { watchlist in
                        HStack(spacing: 10) {
                            Image(systemName: "eye")
                                .foregroundStyle(.secondary)
                            Text(watchlist.name)
                                .lineLimit(1)
                            Spacer()
                            Text("\(watchlist.symbols.count)")
                                .font(.caption2.weight(.semibold))
                                .foregroundStyle(.secondary)
                        }
                        .font(.subheadline)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                    }
                }
            }
            .padding(18)
        }
        .frame(width: 220)
        .background(Color.white.opacity(0.025))
        .accessibilityIdentifier("portfolio.sidebar")
    }

    private func sectionTitle(_ title: String) -> some View {
        Text(title)
            .font(.system(size: 10, weight: .bold))
            .tracking(1.2)
            .foregroundStyle(.tertiary)
    }
}
