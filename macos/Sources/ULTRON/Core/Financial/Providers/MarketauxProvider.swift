import Foundation

/// Marketaux provider — market news and sentiment.
/// Status: Awaiting API validation (credentials provided).
public actor MarketauxProvider: FinancialProvider {
    public let providerID = "marketaux"
    public let providerName = "Marketaux"
    public let financialCapabilities: Set<FinancialCapability> = [.news]
    public let category: ServiceCategory = .custom

    private let token: String
    private let session: URLSession

    public init(token: String? = nil) {
        self.token = token ?? SecretManager.shared.marketauxToken
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { token.isEmpty ? .unhealthy : .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote { throw FinancialError.unsupportedCapability("quotes") }
    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { throw FinancialError.unsupportedCapability("ohlcv") }
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { throw FinancialError.unsupportedCapability("company_profile") }
    public func fetchIndices() async throws -> [MarketIndex] { [] }
    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }
}
