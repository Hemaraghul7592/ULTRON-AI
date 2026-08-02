import SwiftUI

public struct NewsFeedCard: View {
    let news: [NewsArticle]
    let state: DashboardCardState
    let onRefresh: () -> Void
    @Environment(\.openURL) private var openURL

    public var body: some View {
        DashboardCard(title: "News Feed", subtitle: "FinancialEngine news providers", icon: "newspaper.fill", tint: .cyan, state: state) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Spacer()
                    Button("Refresh", action: onRefresh)
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                }
                ForEach(news.prefix(5)) { article in
                    Button {
                        guard let url = URL(string: article.url), !article.url.isEmpty else { return }
                        openURL(url)
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(article.title).font(.subheadline.weight(.semibold)).lineLimit(2)
                            Text("\(article.source.isEmpty ? "Unknown source" : article.source)  |  \(article.publishedAt.formatted(date: .abbreviated, time: .shortened))")
                                .font(.caption).foregroundStyle(.secondary)
                            if !article.summary.isEmpty {
                                Text(article.summary).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Open article \(article.title)")
                }
            }
        }
    }
}
