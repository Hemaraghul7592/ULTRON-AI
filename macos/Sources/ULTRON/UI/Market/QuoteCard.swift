import SwiftUI

public struct QuoteCard: View {
    let quote: Quote?
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Quote", subtitle: "Current market data", icon: "dollarsign.circle.fill", tint: .green, state: state) {
            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    Text(quote?.price.formatted(.currency(code: quote?.currency ?? "USD")) ?? "Unavailable")
                        .font(.system(size: 30, weight: .bold, design: .rounded))
                    Spacer()
                    Text(quote?.timestamp.formatted(date: .omitted, time: .shortened) ?? "")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
                HStack(spacing: 20) {
                    MarketMetric(label: "Change", value: quote.map { $0.change.formatted(.number) }, tint: .green)
                    MarketMetric(label: "Volume", value: quote?.volume.formatted(), tint: .blue)
                    MarketMetric(label: "Exchange", value: quote?.exchange.isEmpty == false ? quote?.exchange : nil, tint: .purple)
                }
            }
        }
    }
}

struct MarketMetric: View {
    let label: String
    let value: String?
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label.uppercased()).font(.system(size: 9, weight: .semibold)).foregroundStyle(.secondary)
            Text(value ?? "Unavailable").font(.subheadline.weight(.semibold)).foregroundStyle(value == nil ? Color.secondary : tint)
        }
    }
}
