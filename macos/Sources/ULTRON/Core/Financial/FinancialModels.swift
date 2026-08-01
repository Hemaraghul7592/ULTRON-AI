import Foundation

// MARK: - Quote

/// A real-time or delayed market quote for a single symbol.
public struct Quote: Sendable, Codable, Equatable {
    public let symbol: String
    public let price: Double
    public let change: Double
    public let changePercent: Double
    public let volume: Int64
    public let timestamp: Date
    public let exchange: String
    public let currency: String

    public init(symbol: String, price: Double, change: Double, changePercent: Double, volume: Int64, timestamp: Date, exchange: String = "", currency: String = "USD") {
        self.symbol = symbol; self.price = price; self.change = change
        self.changePercent = changePercent; self.volume = volume; self.timestamp = timestamp
        self.exchange = exchange; self.currency = currency
    }
}

// MARK: - OHLCV

/// Open-High-Low-Close-Volume bar for a time interval.
public struct OHLCV: Sendable, Codable {
    public let symbol: String
    public let open: Double
    public let high: Double
    public let low: Double
    public let close: Double
    public let volume: Int64
    public let timestamp: Date

    public init(symbol: String, open: Double, high: Double, low: Double, close: Double, volume: Int64, timestamp: Date) {
        self.symbol = symbol; self.open = open; self.high = high; self.low = low
        self.close = close; self.volume = volume; self.timestamp = timestamp
    }
}

// MARK: - Company

/// Fundamental company profile data.
public struct CompanyProfile: Sendable, Codable {
    public let symbol: String
    public let name: String
    public let exchange: String
    public let sector: String
    public let industry: String
    public let marketCap: Double
    public let country: String
    public let currency: String
    public let website: String

    public init(symbol: String, name: String, exchange: String = "", sector: String = "", industry: String = "", marketCap: Double = 0, country: String = "", currency: String = "USD", website: String = "") {
        self.symbol = symbol; self.name = name; self.exchange = exchange
        self.sector = sector; self.industry = industry; self.marketCap = marketCap
        self.country = country; self.currency = currency; self.website = website
    }
}

// MARK: - MarketIndex

/// A market index value at a point in time.
public struct MarketIndex: Sendable, Codable {
    public let symbol: String
    public let name: String
    public let value: Double
    public let change: Double
    public let changePercent: Double
    public let timestamp: Date

    public init(symbol: String, name: String, value: Double, change: Double = 0, changePercent: Double = 0, timestamp: Date = Date()) {
        self.symbol = symbol; self.name = name; self.value = value
        self.change = change; self.changePercent = changePercent; self.timestamp = timestamp
    }
}

// MARK: - News Article

/// A financial news article.
public struct NewsArticle: Sendable, Codable, Identifiable {
    public let id: String
    public let title: String
    public let summary: String
    public let source: String
    public let url: String
    public let publishedAt: Date
    public let relatedSymbols: [String]

    public init(id: String = UUID().uuidString, title: String, summary: String = "", source: String = "", url: String = "", publishedAt: Date = Date(), relatedSymbols: [String] = []) {
        self.id = id; self.title = title; self.summary = summary; self.source = source
        self.url = url; self.publishedAt = publishedAt; self.relatedSymbols = relatedSymbols
    }
}

// MARK: - OHLCV Range

/// Time intervals for OHLCV data requests.
public enum OHLCVRange: String, Sendable, CaseIterable {
    case oneMinute = "1m"
    case fiveMinutes = "5m"
    case fifteenMinutes = "15m"
    case thirtyMinutes = "30m"
    case oneHour = "1h"
    case fourHours = "4h"
    case oneDay = "1d"
    case oneWeek = "1w"
    case oneMonth = "1M"
}
