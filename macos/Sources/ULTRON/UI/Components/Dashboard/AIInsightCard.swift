import SwiftUI

public struct AIInsightCard: View {
    private let insight: AdvisorResponse?
    private let state: DashboardCardState

    public init(insight: AdvisorResponse?, state: DashboardCardState) {
        self.insight = insight
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "AI Daily Insight", subtitle: "Context from your financial data", icon: "sparkles", tint: .pink, state: state) {
            VStack(alignment: .leading, spacing: 14) {
                Text(insight?.summary ?? "No insight available.")
                    .font(.body)
                    .foregroundStyle(.primary)
                    .fixedSize(horizontal: false, vertical: true)

                if let confidence = insight?.confidence, confidence > 0 {
                    HStack(spacing: 8) {
                        Text("Confidence")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        ProgressView(value: confidence)
                            .tint(.pink)
                        Text(confidence.formatted(.percent))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }
}
