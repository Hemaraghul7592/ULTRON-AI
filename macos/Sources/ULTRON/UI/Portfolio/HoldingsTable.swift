import SwiftUI

public struct HoldingsTable: View {
    let rows: [PortfolioHoldingRow]
    let state: DashboardCardState
    let selectedHoldingID: String?
    let onSelect: (String?) -> Void
    @State private var selection = Set<String>()

    public init(rows: [PortfolioHoldingRow], state: DashboardCardState, selectedHoldingID: String?, onSelect: @escaping (String?) -> Void) {
        self.rows = rows
        self.state = state
        self.selectedHoldingID = selectedHoldingID
        self.onSelect = onSelect
    }

    public var body: some View {
        DashboardCard(title: "Holdings", subtitle: "Search, sort, and select a position", icon: "list.bullet.rectangle.fill", tint: .blue, state: state) {
            if rows.isEmpty {
                EmptyStateCard(title: "No holdings match the current filter.", icon: "line.3.horizontal.decrease.circle")
            } else {
                Table(rows, selection: $selection) {
                    TableColumn("Symbol") { row in
                        Text(row.symbol).font(.subheadline.weight(.semibold))
                    }
                    .width(min: 70, ideal: 90)

                    TableColumn("Company") { row in
                        Text(row.companyName).lineLimit(1)
                    }
                    .width(min: 130, ideal: 190)

                    TableColumn("Quantity") { row in
                        Text(row.quantity.formatted())
                    }
                    .width(min: 70, ideal: 90)

                    TableColumn("Average Price") { row in
                        Text(row.averagePrice.formatted(.currency(code: row.currency)))
                    }
                    .width(min: 100, ideal: 125)

                    TableColumn("Current Price") { row in
                        Text(row.currentPrice?.formatted(.currency(code: row.currency)) ?? "Unavailable")
                    }
                    .width(min: 100, ideal: 125)

                    TableColumn("Market Value") { row in
                        Text(row.marketValue?.formatted(.currency(code: row.currency)) ?? "Unavailable")
                    }
                    .width(min: 105, ideal: 135)

                    TableColumn("Today's Change") { row in
                        ChangeLabel(value: row.todaysChangePercent)
                    }
                    .width(min: 100, ideal: 125)

                    TableColumn("Total Return") { row in
                        ChangeLabel(value: row.totalReturn)
                    }
                    .width(min: 95, ideal: 115)

                    TableColumn("Weight") { row in
                        Text(row.weight.map { $0.formatted(.percent) } ?? "Unavailable")
                            .foregroundStyle(.secondary)
                    }
                    .width(min: 70, ideal: 90)
                }
                .frame(minHeight: 240)
                .onChange(of: selection) { _, newValue in
                    onSelect(newValue.first)
                }
                .onChange(of: selectedHoldingID) { _, newValue in
                    selection = newValue.map { [$0] } ?? []
                }
                .contextMenu(forSelectionType: String.self) { selected in
                    if !selected.isEmpty {
                        Button("Select Holding") { onSelect(selected.first) }
                    }
                } primaryAction: { selected in
                    onSelect(selected.first)
                }
                .accessibilityIdentifier("portfolio.holdings.table")
            }
        }
    }
}

private struct ChangeLabel: View {
    let value: Double?

    var body: some View {
        Text(value.map { $0.formatted(.percent) } ?? "Unavailable")
            .foregroundStyle(value.map { $0 >= 0 ? Color.green : Color.red } ?? .secondary)
    }
}
