import SwiftUI

public struct NewsCard: View {
    private let articles: [NewsArticle]
    private let state: DashboardCardState

    public init(articles: [NewsArticle], state: DashboardCardState) {
        self.articles = articles
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "Latest Financial News", subtitle: "Recent market context", icon: "newspaper.fill", tint: .cyan, state: state) {
            VStack(alignment: .leading, spacing: 12) {
                ForEach(articles.prefix(4)) { article in
                    VStack(alignment: .leading, spacing: 3) {
                        Text(article.title)
                            .font(.subheadline.weight(.semibold))
                            .lineLimit(2)
                        Text("\(article.source.isEmpty ? "Unknown source" : article.source)  |  \(article.publishedAt.formatted(date: .abbreviated, time: .shortened))")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    if article.id != articles.prefix(4).last?.id {
                        Divider().opacity(0.45)
                    }
                }
            }
        }
    }
}
