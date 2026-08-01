import Foundation

/// Central SEBI Filings & Disclosures Engine.
///
/// Collects, normalizes, analyzes and exposes regulatory filings.
/// Integrates with AIAdvisorEngine, AlertEngine, and VisualizationEngine.
@MainActor
public final class SEBIEngine {

    private let repository = SEBIRepository()
    private let logger: Logger
    public weak var advisorEngine: AIAdvisorEngine?
    public weak var alertEngine: AlertEngine?

    public init(logger: Logger) { self.logger = logger }

    // MARK: - Ingest

    public func ingest(_ filing: SEBIFiling) async -> Bool {
        let added = await repository.add(filing)
        if added { await logger.info("SEBI filing ingested", metadata: ["symbol": filing.symbol, "category": filing.category.rawValue]) }
        return added
    }

    public func ingestBatch(_ filings: [SEBIFiling]) async -> Int {
        let count = await repository.addBatch(filings)
        await logger.info("SEBI batch ingested", metadata: ["count": "\(count)"])
        return count
    }

    // MARK: - Query

    public func recent(limit: Int = 50) async -> [SEBIFiling] { await repository.recent(limit: limit) }
    public func search(keyword: String) async -> [SEBIFiling] { await repository.search(keyword: keyword) }
    public func bySymbol(_ symbol: String) async -> [SEBIFiling] { await repository.bySymbol(symbol) }
    public func byCategory(_ category: SEBICategory) async -> [SEBIFiling] { await repository.byCategory(category) }
    public func byDateRange(from: Date, to: Date) async -> [SEBIFiling] { await repository.filter(from: from, to: to) }
    public func profile(for symbol: String) async -> SEBICompanyProfile? { await repository.profile(for: symbol) }
    public func allSymbols() async -> [String] { await repository.allSymbols }
    public func filingCount() async -> Int { await repository.count }

    // MARK: - AI Analysis

    /// Generates an AI summary for a filing if advisor is available.
    public func analyze(_ filing: SEBIFiling, using advisor: AIAdvisorEngine? = nil) async -> SEBIAnalysisResult {
        let ai = advisor ?? advisorEngine
        guard let ai else { return SEBIAnalysisResult(filing: filing) }

        let question = """
        Summarize this SEBI filing:
        Company: \(filing.company) (\(filing.symbol))
        Category: \(filing.category.rawValue)
        Title: \(filing.title)
        Content: \(filing.parsedContent.prefix(500))
        Provide: summary, risks, opportunities, market impact, long-term implications.
        """
        let response = await ai.ask(AdvisorRequest(question: question))
        return SEBIAnalysisResult(filing: filing, summary: response.summary, risks: response.risks, opportunities: response.opportunities, marketImpact: "", longTermImplications: "", confidence: response.confidence)
    }

    // MARK: - Alert Integration

    /// Notifies AlertEngine about significant filings.
    public func notifyAlerts(for filing: SEBIFiling) async {
        guard let engine = alertEngine else { return }
        let significant: Set<SEBICategory> = [.insiderTrading, .bulkDeal, .blockDeal, .dividend, .quarterlyResult, .annualReport, .promoterActivity]
        guard significant.contains(filing.category) else { return }

        let symbol = filing.symbol
        engine.addRule(AlertRule(name: "SEBI: \(filing.category.rawValue) - \(symbol)", category: .news, severity: .medium, condition: .alwaysTrue, oneTime: true))
    }

    // MARK: - Portfolio Integration

    /// Returns filings relevant to the given portfolio symbols.
    public func relevantToPortfolio(symbols: [String]) async -> [SEBIFiling] {
        var results: [SEBIFiling] = []
        for sym in symbols { results.append(contentsOf: await repository.bySymbol(sym)) }
        return results.sorted { $0.date > $1.date }
    }

    // MARK: - Visualization Data

    public func timelineData(from: Date, to: Date) async -> [(date: Date, category: SEBICategory, title: String)] {
        let filings = await repository.filter(from: from, to: to)
        return filings.map { ($0.date, $0.category, $0.title) }
    }

    public func filingStats() async -> [(category: SEBICategory, count: Int)] {
        let all = await repository.recent(limit: 10000)
        var stats: [SEBICategory: Int] = [:]
        for f in all { stats[f.category, default: 0] += 1 }
        return stats.sorted { $0.value > $1.value }.map { ($0.key, $0.value) }
    }
}
