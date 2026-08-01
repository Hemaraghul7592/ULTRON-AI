import Foundation

/// Local Ollama LLM provider — runs models on-device.
public actor OllamaProvider: FinancialProvider {
    public let providerID = "ollama"
    public let providerName = "Ollama"
    public let financialCapabilities: Set<FinancialCapability> = [.technicals, .fundamentals]
    public let category: ServiceCategory = .custom

    private let endpoint: String
    private let session: URLSession

    public init(endpoint: String? = nil) {
        self.endpoint = endpoint ?? APIConfiguration.shared.ollamaEndpoint
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus {
        guard let url = URL(string: "\(endpoint)/api/tags") else { return .unhealthy }
        do {
            let (_, resp) = try await session.data(from: url)
            return (resp as? HTTPURLResponse)?.statusCode == 200 ? .healthy : .unhealthy
        } catch { return .unhealthy }
    }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote { throw FinancialError.unsupportedCapability("quotes") }
    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { throw FinancialError.unsupportedCapability("ohlcv") }
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { throw FinancialError.unsupportedCapability("company_profile") }
    public func fetchIndices() async throws -> [MarketIndex] { [] }
    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }
}
