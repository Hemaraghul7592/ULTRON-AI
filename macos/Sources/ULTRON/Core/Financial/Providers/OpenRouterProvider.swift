import Foundation

/// OpenRouter AI provider — routes to multiple LLM backends.
public actor OpenRouterProvider: FinancialProvider {
    public let providerID = "openrouter"
    public let providerName = "OpenRouter"
    public let financialCapabilities: Set<FinancialCapability> = [.technicals, .fundamentals]
    public let category: ServiceCategory = .custom

    private let apiKey: String
    private let session: URLSession

    public init(apiKey: String? = nil) {
        self.apiKey = apiKey ?? SecretManager.shared.openRouterKey
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { apiKey.isEmpty ? .unhealthy : .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote { throw FinancialError.unsupportedCapability("quotes") }
    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { throw FinancialError.unsupportedCapability("ohlcv") }
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { throw FinancialError.unsupportedCapability("company_profile") }
    public func fetchIndices() async throws -> [MarketIndex] { [] }
    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }
}
