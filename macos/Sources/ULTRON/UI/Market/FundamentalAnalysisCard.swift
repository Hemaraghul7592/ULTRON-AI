import SwiftUI

public struct FundamentalAnalysisCard: View {
    let fundamental: MarketFundamentalState
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Fundamental Analysis", subtitle: "FundamentalAnalysisEngine reports", icon: "building.columns.fill", tint: .purple, state: state) {
            VStack(alignment: .leading, spacing: 9) {
                fundamentalRow("Intrinsic Value", fundamental.intrinsicValue?.averageValue)
                fundamentalRow("Valuation", fundamental.valuation?.peRatio)
                fundamentalRow("Growth Score", fundamental.score?.total)
                fundamentalRow("Financial Health", fundamental.score?.rating.rawValue.capitalized)
                fundamentalRow("Profitability", fundamental.profitability?.netMargin)
                fundamentalRow("Cash Flow", fundamental.cashFlow?.freeCashFlow)
                fundamentalRow("Margins", fundamental.profitability?.grossMargin)
                fundamentalRow("Recommendation", fundamental.score?.rating.rawValue.capitalized)
            }
        }
    }

    private func fundamentalRow(_ label: String, _ value: Double?) -> some View {
        HStack {
            Text(label).font(.caption).foregroundStyle(.secondary)
            Spacer()
            Text(value?.formatted(.number.precision(.fractionLength(2))) ?? "Unavailable")
                .font(.caption.weight(.semibold))
                .foregroundStyle(value == nil ? .tertiary : .primary)
        }
    }

    private func fundamentalRow(_ label: String, _ value: String?) -> some View {
        HStack {
            Text(label).font(.caption).foregroundStyle(.secondary)
            Spacer()
            Text(value ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary)
        }
    }
}
