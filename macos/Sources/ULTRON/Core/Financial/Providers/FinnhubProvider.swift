import Foundation

/// Finnhub.io financial data provider.
public actor FinnhubProvider: FinancialProvider {
    public let providerID = "finnhub"
    public let providerName = "Finnhub"
    public let financialCapabilities: Set<FinancialCapability> = [.quotes, .companyProfile, .news, .ohlcv]
    public let category: ServiceCategory = .custom

    private let apiKey: String
    private let session: URLSession
    private let baseURL: String

    public init(apiKey: String? = nil) {
        self.init(apiKey: apiKey ?? SecretManager.shared.finnhubKey, session: URLSession(configuration: .ephemeral), baseURL: "https://finnhub.io/api/v1")
    }

    init(apiKey: String, session: URLSession, baseURL: String = "https://finnhub.io/api/v1") { self.apiKey = apiKey; self.session = session; self.baseURL = baseURL }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { apiKey.isEmpty ? .unhealthy : .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote {
        let url = try ProviderHTTP.makeURL(base: "\(baseURL)/quote", queryItems: [URLQueryItem(name: "symbol", value: symbol), URLQueryItem(name: "token", value: apiKey)])
        var request = URLRequest(url: url); request.httpMethod = "GET"
        let data = try await ProviderHTTP.data(from: request, session: session, provider: providerID)
        let fq = try ProviderHTTP.decode(FinnhubQuote.self, data: data, provider: providerID)
        return Quote(symbol: symbol, price: fq.c, change: fq.d, changePercent: fq.dp, volume: 0, timestamp: Date(), exchange: "", currency: "USD")
    }

    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] {
        let resolution = rangeToResolution(range)
        let to = Int(Date().timeIntervalSince1970)
        let from = to - (resolution == "D" ? 86400 * 30 : 3600)
        let url = try ProviderHTTP.makeURL(base: "\(baseURL)/stock/candle", queryItems: [URLQueryItem(name: "symbol", value: symbol), URLQueryItem(name: "resolution", value: resolution), URLQueryItem(name: "from", value: "\(from)"), URLQueryItem(name: "to", value: "\(to)"), URLQueryItem(name: "token", value: apiKey)])
        var request = URLRequest(url: url); request.httpMethod = "GET"
        let data = try await ProviderHTTP.data(from: request, session: session, provider: providerID)
        let result = try ProviderHTTP.decode(FinnhubCandles.self, data: data, provider: providerID)
        guard result.s == "ok" else { throw FinancialError.invalidData("Finnhub: \(result.s)") }
        guard let timestamps = result.t, let opens = result.o, let highs = result.h, let lows = result.l, let closes = result.c,
              timestamps.count == opens.count, opens.count == highs.count, highs.count == lows.count, lows.count == closes.count else {
            throw FinancialError.invalidResponse("\(providerID) candle arrays have inconsistent lengths")
        }
        var bars: [OHLCV] = []
        for i in timestamps.indices {
            bars.append(OHLCV(symbol: symbol, open: opens[i], high: highs[i], low: lows[i], close: closes[i], volume: 0, timestamp: Date(timeIntervalSince1970: Double(timestamps[i]))))
        }
        return bars
    }

    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        let url = try ProviderHTTP.makeURL(base: "\(baseURL)/stock/profile2", queryItems: [URLQueryItem(name: "symbol", value: symbol), URLQueryItem(name: "token", value: apiKey)])
        var request = URLRequest(url: url); request.httpMethod = "GET"
        let data = try await ProviderHTTP.data(from: request, session: session, provider: providerID)
        let p = try ProviderHTTP.decode(FinnhubProfile.self, data: data, provider: providerID)
        return CompanyProfile(symbol: symbol, name: p.name, exchange: p.exchange, sector: p.finnhubIndustry, marketCap: p.marketCapitalization * 1_000_000, country: p.country, currency: p.currency, website: p.weburl)
    }

    public func fetchIndices() async throws -> [MarketIndex] { [] }
    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] {
        guard !apiKey.isEmpty else { return [] }
        var results: [NewsArticle] = []
        for sym in symbols.prefix(3) {
            let from = ISO8601DateFormatter().string(from: Date().addingTimeInterval(-7 * 86400))
            let to = ISO8601DateFormatter().string(from: Date())
            let url = try ProviderHTTP.makeURL(base: "\(baseURL)/company-news", queryItems: [URLQueryItem(name: "symbol", value: sym), URLQueryItem(name: "from", value: from), URLQueryItem(name: "to", value: to), URLQueryItem(name: "token", value: apiKey)])
            var request = URLRequest(url: url); request.httpMethod = "GET"
            let data = try await ProviderHTTP.data(from: request, session: session, provider: providerID)
            let items = try ProviderHTTP.decode([FinnhubNewsItem].self, data: data, provider: providerID)
            for item in items.prefix(5) {
                results.append(NewsArticle(title: item.headline, summary: item.summary, source: item.source, url: item.url, publishedAt: Date(timeIntervalSince1970: Double(item.datetime)), relatedSymbols: [sym]))
            }
        }
        return results
    }

    private func rangeToResolution(_ range: OHLCVRange) -> String {
        switch range { case .oneMinute: "1"; case .fiveMinutes: "5"; case .fifteenMinutes: "15"; case .thirtyMinutes: "30"; case .oneHour: "60"; case .fourHours: "240"; case .oneDay: "D"; case .oneWeek: "W"; case .oneMonth: "M" }
    }
}

private struct FinnhubQuote: Decodable { let c: Double; let d: Double; let dp: Double }
private struct FinnhubCandles: Decodable { let s: String; let t: [Int]?; let o: [Double]?; let h: [Double]?; let l: [Double]?; let c: [Double]? }
private struct FinnhubProfile: Decodable { let name: String; let exchange: String; let finnhubIndustry: String; let marketCapitalization: Double; let country: String; let currency: String; let weburl: String }
private struct FinnhubNewsItem: Decodable { let headline: String; let summary: String; let source: String; let url: String; let datetime: Int }
