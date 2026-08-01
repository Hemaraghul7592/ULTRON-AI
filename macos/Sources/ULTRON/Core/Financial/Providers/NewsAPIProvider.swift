import Foundation

/// NewsAPI.org provider for financial news.
public actor NewsAPIProvider: FinancialProvider {
    public let providerID = "newsapi"
    public let providerName = "NewsAPI"
    public let financialCapabilities: Set<FinancialCapability> = [.news]
    public let category: ServiceCategory = .custom

    private let apiKey: String
    private let session: URLSession

    public init(apiKey: String? = nil) {
        self.apiKey = apiKey ?? APIConfiguration.shared.newsAPIKey
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { apiKey.isEmpty ? .unhealthy : .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote { throw FinancialError.unsupportedCapability("quotes") }
    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { throw FinancialError.unsupportedCapability("ohlcv") }
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { throw FinancialError.unsupportedCapability("company_profile") }
    public func fetchIndices() async throws -> [MarketIndex] { [] }

    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] {
        guard !apiKey.isEmpty else { return [] }
        let query = symbols.joined(separator: " OR ")
        let from = ISO8601DateFormatter().string(from: Date().addingTimeInterval(-7 * 86400))
        let url = URL(string: "https://newsapi.org/v2/everything?q=\(query)&from=\(from)&sortBy=publishedAt&pageSize=10&apiKey=\(apiKey)")!
        let encoded = url.absoluteString.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? url.absoluteString
        let (data, _) = try await session.data(from: URL(string: encoded) ?? url)
        let result = try JSONDecoder().decode(NewsAPIResponse.self, from: data)
        return result.articles.map { a in
            NewsArticle(title: a.title, summary: a.description ?? "", source: a.source.name, url: a.url, publishedAt: ISO8601DateFormatter().date(from: a.publishedAt) ?? Date(), relatedSymbols: symbols)
        }
    }
}

private struct NewsAPIResponse: Decodable { let articles: [NewsAPIArticle] }
private struct NewsAPIArticle: Decodable { let title: String; let description: String?; let url: String; let publishedAt: String; let source: NewsAPISource }
private struct NewsAPISource: Decodable { let name: String }
