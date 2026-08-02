import SwiftUI

public struct AIContextCard: View {
    let context: AIWorkspaceContext
    public var body: some View { VStack(alignment: .leading, spacing: 7) { Text("ACTIVE CONTEXT").font(.system(size: 10, weight: .bold)).tracking(1.2).foregroundStyle(.tertiary); row("Portfolio", context.portfolio == nil ? nil : "Available"); row("Watchlists", context.watchlists.isEmpty ? nil : "Available"); row("Market", context.marketIndices.isEmpty ? nil : "Available"); row("News", context.news.isEmpty ? nil : "Available"); row("Technicals", context.technicalSummary) ; row("Alerts", context.alerts.isEmpty ? nil : "Available") }.font(.caption) }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).foregroundStyle(.secondary); Spacer(); Text(value ?? "Unavailable").foregroundStyle(value == nil ? .tertiary : .primary) } }
}
