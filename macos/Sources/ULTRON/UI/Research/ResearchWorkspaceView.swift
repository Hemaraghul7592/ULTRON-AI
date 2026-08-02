import AppKit
import SwiftUI

public struct ResearchWorkspaceView: View {
    @StateObject private var viewModel: ResearchWorkspaceViewModel
    public init(viewModel: ResearchWorkspaceViewModel) { _viewModel = StateObject(wrappedValue: viewModel) }

    public var body: some View {
        HStack(spacing: 0) {
            ResearchSidebar(searchQuery: $viewModel.searchQuery, favorites: viewModel.favoriteSymbols, recent: viewModel.recentSymbols, selectedSymbol: viewModel.symbol, onSearch: { Task { await viewModel.search() } }, onSelect: { symbol in Task { await viewModel.selectSymbol(symbol) } })
            Divider()
            main
        }
        .background(Color.black.opacity(0.94))
        .task { if viewModel.loadingState == .idle && !viewModel.searchQuery.isEmpty { await viewModel.search() } }
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("research.workspace")
    }

    @ViewBuilder private var main: some View {
        switch viewModel.loadingState {
        case .idle, .loading: ProgressView("Loading research...").frame(maxWidth: .infinity, maxHeight: .infinity)
        case .empty: EmptyResearchView()
        case .failed(let message): ContentUnavailableView { Label("Research unavailable", systemImage: "exclamationmark.triangle") } description: { Text(message) } actions: { Button("Retry") { Task { await viewModel.refresh() } } }.frame(maxWidth: .infinity, maxHeight: .infinity)
        case .refreshing, .loaded: loaded
        }
    }

    private var loaded: some View {
        VStack(alignment: .leading, spacing: 16) {
            ResearchHeader(company: viewModel.company, quote: viewModel.quote, isFavorite: viewModel.symbol.map(viewModel.favoriteSymbols.contains) ?? false, lastUpdated: viewModel.lastUpdated, onRefresh: { Task { await viewModel.refresh() } }, onFavorite: viewModel.toggleFavorite)
            ResearchSearchBar(query: $viewModel.searchQuery) { Task { await viewModel.search() } }
            ScrollView {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 320, maximum: 620), spacing: 16)], alignment: .leading, spacing: 16) {
                    CompanySnapshotCard(company: viewModel.company, quote: viewModel.quote, state: cardState(viewModel.company != nil))
                    BusinessSummaryCard(company: viewModel.company, state: cardState(viewModel.company != nil))
                    FinancialHealthCard(fundamental: viewModel.fundamental, state: .empty)
                    ValuationCard(fundamental: viewModel.fundamental, state: .empty)
                    GrowthCard(fundamental: viewModel.fundamental, state: .empty)
                    ProfitabilityCard(fundamental: viewModel.fundamental, state: .empty)
                    RiskCard(exposure: viewModel.portfolioExposure, analysis: viewModel.aiResearch, state: cardState(viewModel.portfolioExposure != nil || viewModel.aiResearch != nil))
                    TechnicalSummaryCard(technical: viewModel.technical, state: cardState(viewModel.technical.signal != nil || viewModel.technical.rsi != nil))
                    NewsSummaryCard(news: viewModel.news, timeline: viewModel.timeline, state: cardState(!viewModel.news.isEmpty), onRefresh: { Task { await viewModel.refreshNews() } })
                    AIResearchCard(analysis: viewModel.aiResearch, state: cardState(viewModel.aiResearch != nil), onRefresh: { Task { await viewModel.refreshAIAnalysis() } })
                    InvestmentChecklistCard(items: viewModel.checklist, state: cardState(!viewModel.checklist.isEmpty))
                    CompetitorComparisonCard(state: .empty)
                    ResearchTimelineCard(events: viewModel.timeline, state: cardState(!viewModel.timeline.isEmpty))
                    ResearchNotesCard(notes: $viewModel.notes, state: .loaded, onSave: viewModel.saveNotes)
                    ResearchExportCard(onCopy: { copy(viewModel.copySummary()) }, onMarkdown: { copy(viewModel.exportMarkdown()) }, onJSON: { if let data = viewModel.exportJSON() { copy(String(decoding: data, as: UTF8.self)) } })
                }
                .padding(.bottom, 20)
            }
            .scrollIndicators(.hidden)
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    private func cardState(_ hasContent: Bool) -> DashboardCardState {
        switch viewModel.loadingState { case .idle, .loading: .loading; case .refreshing: hasContent ? .loaded : .loading; case .loaded: hasContent ? .loaded : .empty; case .empty: .empty; case .failed(let message): .failed(message) }
    }
    private func copy(_ text: String) { NSPasteboard.general.clearContents(); NSPasteboard.general.setString(text, forType: .string) }
}

#if DEBUG
#Preview("Research Empty") { ResearchWorkspaceView(viewModel: ResearchPreviewFactory.make(state: .empty)).frame(width: 1280, height: 800) }
#Preview("Research Loading") { ResearchWorkspaceView(viewModel: ResearchPreviewFactory.make(state: .loading)).frame(width: 900, height: 650) }
#Preview("Research Error") { ResearchWorkspaceView(viewModel: ResearchPreviewFactory.make(state: .failed("Preview error"))).frame(width: 1440, height: 900) }
#endif
