import Foundation

/// Binance cryptocurrency data provider.
public actor BinanceProvider: FinancialProvider {
    public let providerID = "binance"
    public let providerName = "Binance"
    public let financialCapabilities: Set<FinancialCapability> = [.quotes, .ohlcv, .crypto]
    public let category: ServiceCategory = .custom

    private let session: URLSession

    public init() {
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote {
        let sym = symbol.uppercased() + "USDT"
        let url = URL(string: "https://api.binance.com/api/v3/ticker/24hr?symbol=\(sym)")!
        let (data, _) = try await session.data(from: url)
        let ticker = try JSONDecoder().decode(BinanceTicker.self, from: data)
        return Quote(symbol: symbol, price: Double(ticker.lastPrice) ?? 0, change: Double(ticker.priceChange) ?? 0, changePercent: Double(ticker.priceChangePercent) ?? 0, volume: Int64(Double(ticker.volume) ?? 0), timestamp: Date(), exchange: "Binance", currency: "USDT")
    }

    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] {
        let sym = symbol.uppercased() + "USDT"
        let interval = rangeToBinance(range)
        let url = URL(string: "https://api.binance.com/api/v3/klines?symbol=\(sym)&interval=\(interval)&limit=50")!
        let (data, _) = try await session.data(from: url)
        let klines = try JSONDecoder().decode([[BinanceKlineValue]].self, from: data)
        return klines.map { k in
            OHLCV(symbol: symbol, open: Double(k[1].value)!, high: Double(k[2].value)!, low: Double(k[3].value)!, close: Double(k[4].value)!, volume: Int64(Double(k[5].value)!), timestamp: Date(timeIntervalSince1970: Double(k[0].value)! / 1000))
        }
    }

    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { throw FinancialError.unsupportedCapability("company_profile") }
    public func fetchIndices() async throws -> [MarketIndex] { [] }
    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }

    private func rangeToBinance(_ range: OHLCVRange) -> String {
        switch range { case .oneMinute: "1m"; case .fiveMinutes: "5m"; case .fifteenMinutes: "15m"; case .thirtyMinutes: "30m"; case .oneHour: "1h"; case .fourHours: "4h"; case .oneDay: "1d"; case .oneWeek: "1w"; case .oneMonth: "1M" }
    }
}

private struct BinanceTicker: Decodable { let lastPrice: String; let priceChange: String; let priceChangePercent: String; let volume: String }
private struct BinanceKlineValue: Decodable { let value: String; init(from decoder: Decoder) throws { let c = try decoder.singleValueContainer(); value = try c.decode(String.self) } }
