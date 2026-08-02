import SwiftUI

public struct TransactionHistoryCard: View {
    let transactions: [Transaction]
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Transaction History", subtitle: "Recent portfolio activity", icon: "arrow.left.arrow.right", tint: .orange, state: state) {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(Array(transactions.suffix(6).reversed())) { transaction in
                    HStack(spacing: 10) {
                        Image(systemName: icon(for: transaction.type))
                            .foregroundStyle(transaction.type == .sell ? .red : .green)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("\(transaction.type.rawValue.capitalized) \(transaction.symbol)")
                                .font(.subheadline.weight(.semibold))
                            Text(transaction.timestamp.formatted(date: .abbreviated, time: .shortened))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text(transaction.totalValue.formatted(.currency(code: transaction.currency)))
                            .font(.subheadline.weight(.medium))
                    }
                }
            }
        }
    }

    private func icon(for type: TransactionType) -> String {
        switch type {
        case .buy: "arrow.down.left"
        case .sell: "arrow.up.right"
        case .deposit: "plus.circle"
        case .withdrawal: "minus.circle"
        default: "circle"
        }
    }
}
