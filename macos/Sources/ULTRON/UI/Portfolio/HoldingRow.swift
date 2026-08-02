import SwiftUI

public struct HoldingRow: View {
    let row: PortfolioHoldingRow

    public var body: some View {
        HStack {
            Text(row.symbol).font(.subheadline.weight(.semibold))
            Text(row.companyName).foregroundStyle(.secondary)
            Spacer()
            Text(row.marketValue?.formatted(.currency(code: row.currency)) ?? "Unavailable")
        }
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Holding \(row.symbol), \(row.companyName)")
    }
}
