/// Capabilities that a financial provider can support.
public struct FinancialCapability: Sendable, Hashable {
    public let rawValue: String
    public init(_ rawValue: String) { self.rawValue = rawValue }

    public static let quotes = FinancialCapability("quotes")
    public static let ohlcv = FinancialCapability("ohlcv")
    public static let companyProfile = FinancialCapability("company_profile")
    public static let marketIndices = FinancialCapability("market_indices")
    public static let news = FinancialCapability("news")
    public static let crypto = FinancialCapability("crypto")
    public static let fundamentals = FinancialCapability("fundamentals")
    public static let technicals = FinancialCapability("technicals")
    public static let screening = FinancialCapability("screening")
}

/// Protocol for financial data providers.
///
/// Conforming types provide typed methods for financial data access.
/// Providers also conform to `ServiceProvider` for integration with
/// the `ServiceOrchestrator` (retry, failover, circuit breaking).
public protocol FinancialProvider: ServiceProvider {

    /// The capabilities this provider supports.
    var financialCapabilities: Set<FinancialCapability> { get }

    /// Fetches a real-time quote for a symbol.
    func fetchQuote(symbol: String) async throws -> Quote

    /// Fetches OHLCV bars for a symbol and range.
    func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV]

    /// Fetches company profile data.
    func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile

    /// Fetches market indices.
    func fetchIndices() async throws -> [MarketIndex]

    /// Fetches financial news.
    func fetchNews(symbols: [String]) async throws -> [NewsArticle]
}

// MARK: - Default Implementations

public extension FinancialProvider {
    var category: ServiceCategory { .custom }
    var capabilities: Set<ServiceCapability> { [] }

    func execute(request: any Sendable) async throws -> any Sendable {
        throw FinancialError.unsupportedCapability("Use typed methods")
    }
}
