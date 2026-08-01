import Foundation

/// HackerEarth provider — code evaluation platform.
/// Status: Registered, awaiting endpoint configuration.
public actor HackerEarthProvider: FinancialProvider {
    public let providerID = "hackerearth"
    public let providerName = "HackerEarth"
    public let financialCapabilities: Set<FinancialCapability> = []
    public let category: ServiceCategory = .custom

    private let clientID: String
    private let secret: String
    private let session: URLSession

    public init(clientID: String? = nil, secret: String? = nil) {
        self.clientID = clientID ?? APIConfiguration.shared.hackerEarthKey
        self.secret = secret ?? APIConfiguration.shared.hackerEarthSecret
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { clientID.isEmpty ? .unhealthy : .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote { throw FinancialError.unsupportedCapability("quotes") }
    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { throw FinancialError.unsupportedCapability("ohlcv") }
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { throw FinancialError.unsupportedCapability("company_profile") }
    public func fetchIndices() async throws -> [MarketIndex] { [] }
    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }
}
