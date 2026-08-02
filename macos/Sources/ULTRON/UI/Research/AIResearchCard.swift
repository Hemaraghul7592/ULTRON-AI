import SwiftUI

public struct AIResearchCard: View {
    let analysis: AdvisorResponse?; let state: DashboardCardState; let onRefresh: () -> Void
    public var body: some View { DashboardCard(title: "AI Research", subtitle: "AIAdvisorEngine", icon: "sparkles", tint: .pink, state: state) { VStack(alignment: .leading, spacing: 9) { HStack { Spacer(); Button("Refresh", action: onRefresh).buttonStyle(.bordered).controlSize(.small) }; Text(analysis?.summary ?? "No AI research available.").font(.subheadline).fixedSize(horizontal: false, vertical: true); section("Bull Case", analysis?.opportunities ?? []); section("Bear Case / Risks", analysis?.risks ?? []); section("Investment Thesis", analysis?.analysis.isEmpty == false ? [analysis?.analysis ?? ""] : []); section("Suggested Strategy", analysis?.suggestedActions ?? []); if let confidence = analysis?.confidence, confidence > 0 { Text("Confidence \(confidence.formatted(.percent))").font(.caption).foregroundStyle(.secondary) } } } }
    @ViewBuilder private func section(_ title: String, _ values: [String]) -> some View { if !values.isEmpty { VStack(alignment: .leading, spacing: 3) { Text(title).font(.caption.weight(.bold)).foregroundStyle(.secondary); ForEach(values, id: \.self) { Text($0).font(.caption) } } } }
}
