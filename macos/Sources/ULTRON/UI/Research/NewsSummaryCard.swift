import SwiftUI

public struct NewsSummaryCard: View {
    let news: [NewsArticle]; let timeline: [ResearchTimelineEvent]; let state: DashboardCardState; let onRefresh: () -> Void
    @Environment(\.openURL) private var openURL
    public var body: some View { DashboardCard(title: "News Summary", subtitle: "FinancialEngine news timeline", icon: "newspaper.fill", tint: .cyan, state: state) { VStack(alignment: .leading, spacing: 10) { HStack { Spacer(); Button("Refresh", action: onRefresh).buttonStyle(.bordered).controlSize(.small) }; ForEach(news.prefix(4)) { article in Button { if let url = URL(string: article.url), !article.url.isEmpty { openURL(url) } } label: { VStack(alignment: .leading, spacing: 3) { Text(article.title).font(.caption.weight(.semibold)).lineLimit(2); Text("\(article.source.isEmpty ? "Unknown source" : article.source) | \(article.publishedAt.formatted(date: .abbreviated, time: .shortened))").font(.caption2).foregroundStyle(.secondary); if !article.summary.isEmpty { Text(article.summary).font(.caption2).foregroundStyle(.secondary).lineLimit(2) } }.frame(maxWidth: .infinity, alignment: .leading) }.buttonStyle(.plain) } } } }
}
