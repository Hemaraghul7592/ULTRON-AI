import Foundation

/// SEBI data provider implementing FinancialProvider.
/// Currently uses local data/parsing. Network endpoints to be added when available.
public actor SEBIProvider: FinancialProvider {
    public let providerID = "sebi"
    public let providerName = "SEBI"
    public let financialCapabilities: Set<FinancialCapability> = [.fundamentals, .news]
    public let category: ServiceCategory = .custom

    public init() {}

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { .healthy }
    public func shutdown() async {}

    public func fetchQuote(symbol: String) async throws -> Quote { throw FinancialError.unsupportedCapability("quotes") }
    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { throw FinancialError.unsupportedCapability("ohlcv") }
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { throw FinancialError.unsupportedCapability("company_profile") }
    public func fetchIndices() async throws -> [MarketIndex] { [] }

    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] {
        []  // SEBI filings are structured documents, not news
    }
}
