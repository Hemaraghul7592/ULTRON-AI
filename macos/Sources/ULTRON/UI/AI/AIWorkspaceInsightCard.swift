import SwiftUI

public struct AIWorkspaceInsightCard: View {
    let response: AdvisorResponse
    public var body: some View { VStack(alignment: .leading, spacing: 12) { Label("ULTRON Insight", systemImage: "sparkles").font(.headline).foregroundStyle(.pink); Text(response.summary).font(.body).textSelection(.enabled); section("Reasoning", response.analysis); section("Risks", response.risks.joined(separator: "\n")); section("Next actions", response.suggestedActions.joined(separator: "\n")); if response.confidence > 0 { Text("Confidence \(response.confidence.formatted(.percent))").font(.caption).foregroundStyle(.secondary) } }.padding(18).background(Color.pink.opacity(0.07), in: RoundedRectangle(cornerRadius: 16, style: .continuous)).accessibilityIdentifier("ai.insight") }
    @ViewBuilder private func section(_ title: String, _ text: String) -> some View { if !text.isEmpty { VStack(alignment: .leading, spacing: 4) { Text(title).font(.caption.weight(.bold)).foregroundStyle(.secondary); Text(text).font(.caption).textSelection(.enabled) } } }
}
