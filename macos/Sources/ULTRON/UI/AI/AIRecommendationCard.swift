import SwiftUI

public struct AIRecommendationCard: View {
    let recommendations: [Recommendation]
    public var body: some View { VStack(alignment: .leading, spacing: 9) { Label("Recommendations", systemImage: "checkmark.seal.fill").font(.headline); ForEach(recommendations) { recommendation in Text(recommendation.title).font(.caption) } }.padding(16).background(Color.white.opacity(0.05), in: RoundedRectangle(cornerRadius: 14, style: .continuous)) }
}
