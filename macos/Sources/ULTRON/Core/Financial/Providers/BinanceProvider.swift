import Foundation

/// Binance cryptocurrency data provider.
public actor BinanceProvider: FinancialProvider {
    public let providerID = "binance"
    public let providerName = "Binance"
    public let financialCapabilities: Set<FinancialCapability> = [.quotes, .ohlcv, .crypto]
    public let category: ServiceCategory = .custom

    private let session: URLSession
    private let baseURL: String

    public init() {
        self.init(session: URLSession(configuration: .ephemeral), baseURL: "https://api.binance.com")
    }

    init(session: URLSession, baseURL: String = "https://api.binance.com") { self.session = session; self.baseURL = baseURL }

    public func initialize() async throws {}
    public func healthCheck() async -> HealthStatus { .healthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote {
        let sym = symbol.uppercased() + "USDT"
        let url = try ProviderHTTP.makeURL(base: "\(baseURL)/api/v3/ticker/24hr", queryItems: [URLQueryItem(name: "symbol", value: sym)])
        var request = URLRequest(url: url); request.httpMethod = "GET"
        let data = try await ProviderHTTP.data(from: request, session: session, provider: providerID)
        let ticker = try ProviderHTTP.decode(BinanceTicker.self, data: data, provider: providerID)
        guard let price = Double(ticker.lastPrice), let change = Double(ticker.priceChange), let changePercent = Double(ticker.priceChangePercent), let volume = Double(ticker.volume), volume >= 0 else {
            throw FinancialError.invalidResponse("\(providerID) returned invalid numeric quote fields")
        }
        return Quote(symbol: symbol, price: price, change: change, changePercent: changePercent, volume: Int64(volume), timestamp: Date(), exchange: "Binance", currency: "USDT")
    }

    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] {
        let sym = symbol.uppercased() + "USDT"
        let interval = rangeToBinance(range)
        let url = try ProviderHTTP.makeURL(base: "\(baseURL)/api/v3/klines", queryItems: [URLQueryItem(name: "symbol", value: sym), URLQueryItem(name: "interval", value: interval), URLQueryItem(name: "limit", value: "50")])
        var request = URLRequest(url: url); request.httpMethod = "GET"
        let data = try await ProviderHTTP.data(from: request, session: session, provider: providerID)
        let klines = try ProviderHTTP.decode([[BinanceKlineValue]].self, data: data, provider: providerID)
        var bars: [OHLCV] = []
        for kline in klines {
            guard kline.count >= 6,
                  let timestamp = Double(kline[0].value),
                  let open = Double(kline[1].value),
                  let high = Double(kline[2].value),
                  let low = Double(kline[3].value),
                  let close = Double(kline[4].value),
                  let volume = Double(kline[5].value),
                  volume >= 0 else {
                throw FinancialError.invalidResponse("\(providerID) returned an invalid kline")
            }
            bars.append(OHLCV(symbol: symbol, open: open, high: high, low: low, close: close, volume: Int64(volume), timestamp: Date(timeIntervalSince1970: timestamp / 1000)))
        }
        return bars
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
