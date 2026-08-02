import SwiftUI

public struct AIAnalysisCard: View {
    let analysis: AdvisorResponse?
    let state: DashboardCardState
    let onRefresh: () -> Void

    public var body: some View {
        DashboardCard(title: "AI Analysis", subtitle: "AIAdvisorEngine response", icon: "sparkles", tint: .pink, state: state) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Spacer()
                    Button("Refresh", action: onRefresh).buttonStyle(.bordered).controlSize(.small)
                }
                Text(analysis?.summary ?? "No AI analysis available.")
                    .font(.subheadline)
                    .fixedSize(horizontal: false, vertical: true)
                analysisSection("Strengths", analysis?.opportunities ?? [])
                analysisSection("Weaknesses", analysis?.analysis.isEmpty == false ? [analysis?.analysis ?? ""] : [])
                analysisSection("Opportunities", analysis?.opportunities ?? [])
                analysisSection("Risks", analysis?.risks ?? [])
                analysisSection("Suggested action", analysis?.suggestedActions ?? [])
            }
        }
    }

    @ViewBuilder
    private func analysisSection(_ title: String, _ values: [String]) -> some View {
        if !values.isEmpty {
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.caption.weight(.bold)).foregroundStyle(.secondary)
                ForEach(values, id: \.self) { Text($0).font(.caption) }
            }
        }
    }
}
