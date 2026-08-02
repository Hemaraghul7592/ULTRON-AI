import SwiftUI

public struct ValuationCard: View {
    let fundamental: ResearchFundamentalState; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Valuation", subtitle: "FundamentalAnalysisEngine", icon: "chart.bar.doc.horizontal.fill", tint: .purple, state: state) { VStack(spacing: 9) { row("Intrinsic Value", fundamental.intrinsicValue?.averageValue); row("DCF", fundamental.intrinsicValue?.dcfValue); row("Graham Value", fundamental.intrinsicValue?.grahamValue); row("Margin of Safety", fundamental.intrinsicValue?.marginOfSafety); row("Recommendation", fundamental.score?.rating.rawValue.capitalized) } } }
    private func row(_ label: String, _ value: Double?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value?.formatted(.number.precision(.fractionLength(2))) ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
}
