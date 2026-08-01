import Foundation

/// Finnhub.io financial data provider.
public actor FinnhubProvider: FinancialProvider {
    public let providerID = "finnhub"
    public let providerName = "Finnhub"
    public let financialCapabilities: Set<FinancialCapability> = [.quotes, .companyProfile, .news, .ohlcv]
    public let category: ServiceCategory = .custom

    private let apiKey: String
    private let session: URLSession
    private let baseURL = "https://finnhub.io/api/v1"

    public init(apiKey: String? = nil) {
        self.apiKey = apiKey ?? APIConfiguration.shared.finnhubKey
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { apiKey.isEmpty ? .unhealthy : .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote {
        let url = URL(string: "\(baseURL)/quote?symbol=\(symbol)&token=\(apiKey)")!
        let (data, _) = try await session.data(from: url)
        let fq = try JSONDecoder().decode(FinnhubQuote.self, from: data)
        return Quote(symbol: symbol, price: fq.c, change: fq.d, changePercent: fq.dp, volume: 0, timestamp: Date(), exchange: "", currency: "USD")
    }

    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] {
        let resolution = rangeToResolution(range)
        let to = Int(Date().timeIntervalSince1970)
        let from = to - (resolution == "D" ? 86400 * 30 : 3600)
        let url = URL(string: "\(baseURL)/stock/candle?symbol=\(symbol)&resolution=\(resolution)&from=\(from)&to=\(to)&token=\(apiKey)")!
        let (data, _) = try await session.data(from: url)
        let result = try JSONDecoder().decode(FinnhubCandles.self, from: data)
        guard result.s == "ok" else { throw FinancialError.invalidData("Finnhub: \(result.s)") }
        var bars: [OHLCV] = []
        for i in 0..<min(result.t?.count ?? 0, result.o?.count ?? 0) {
            bars.append(OHLCV(symbol: symbol, open: result.o![i], high: result.h![i], low: result.l![i], close: result.c![i], volume: 0, timestamp: Date(timeIntervalSince1970: Double(result.t![i]))))
        }
        return bars
    }

    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        let url = URL(string: "\(baseURL)/stock/profile2?symbol=\(symbol)&token=\(apiKey)")!
        let (data, _) = try await session.data(from: url)
        let p = try JSONDecoder().decode(FinnhubProfile.self, from: data)
        return CompanyProfile(symbol: symbol, name: p.name, exchange: p.exchange, sector: p.finnhubIndustry, marketCap: p.marketCapitalization * 1_000_000, country: p.country, currency: p.currency, website: p.weburl)
    }

    public func fetchIndices() async throws -> [MarketIndex] { [] }
    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] {
        guard !apiKey.isEmpty else { return [] }
        var results: [NewsArticle] = []
        for sym in symbols.prefix(3) {
            let from = ISO8601DateFormatter().string(from: Date().addingTimeInterval(-7 * 86400))
            let to = ISO8601DateFormatter().string(from: Date())
            let url = URL(string: "\(baseURL)/company-news?symbol=\(sym)&from=\(from)&to=\(to)&token=\(apiKey)")!
            let (data, _) = try await session.data(from: url)
            let items = (try? JSONDecoder().decode([FinnhubNewsItem].self, from: data)) ?? []
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
