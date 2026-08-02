import SwiftUI

public struct PortfolioAIReviewCard: View {
    let review: AdvisorResponse?
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "AI Portfolio Review", subtitle: "Advisor response for this portfolio", icon: "sparkles", tint: .pink, state: state) {
            VStack(alignment: .leading, spacing: 12) {
                Text(review?.summary ?? "No AI review available.")
                    .font(.subheadline)
                    .fixedSize(horizontal: false, vertical: true)
                reviewSection("Strengths", values: review?.opportunities ?? [])
                reviewSection("Weaknesses", values: review?.analysis.isEmpty == false ? [review?.analysis ?? ""] : [])
                reviewSection("Risk observations", values: review?.risks ?? [])
                reviewSection("Suggestions", values: review?.suggestedActions ?? [])
                reviewSection("Diversification recommendations", values: review?.suggestedActions ?? [])
            }
        }
    }

    @ViewBuilder
    private func reviewSection(_ title: String, values: [String]) -> some View {
        if !values.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(.caption.weight(.bold)).foregroundStyle(.secondary)
                ForEach(values, id: \.self) { value in
                    Text(value).font(.caption)
                }
            }
        }
    }
}
