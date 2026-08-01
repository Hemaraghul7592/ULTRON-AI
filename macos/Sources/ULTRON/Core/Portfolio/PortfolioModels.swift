import Foundation

// MARK: - Transaction

public struct Transaction: Sendable, Codable, Identifiable {
    public let id: String
    public let type: TransactionType
    public let symbol: String
    public let quantity: Double
    public let price: Double
    public let currency: String
    public let broker: String
    public let exchange: String
    public let timestamp: Date
    public let notes: String

    public var totalValue: Double { quantity * price }

    public init(id: String = UUID().uuidString, type: TransactionType, symbol: String, quantity: Double, price: Double, currency: String = "USD", broker: String = "", exchange: String = "", timestamp: Date = Date(), notes: String = "") {
        self.id = id; self.type = type; self.symbol = symbol; self.quantity = quantity; self.price = price
        self.currency = currency; self.broker = broker; self.exchange = exchange; self.timestamp = timestamp; self.notes = notes
    }
}

public enum TransactionType: String, Sendable, Codable, CaseIterable {
    case buy, sell, dividend, bonus, split, rightsIssue, interest, deposit, withdrawal, fee, tax
    public var affectsHoldings: Bool { self == .buy || self == .sell || self == .bonus || self == .split }
}

// MARK: - Holding

public struct Holding: Sendable, Codable, Identifiable {
    public let id: String
    public let symbol: String
    public var quantity: Double
    public var averagePrice: Double
    public var currentPrice: Double?
    public let currency: String

    public var costBasis: Double { quantity * averagePrice }
    public var currentValue: Double? { currentPrice.map { quantity * $0 } }
    public var unrealizedPL: Double? { currentValue.map { $0 - costBasis } }
    public var unrealizedPLPercent: Double? { costBasis > 0 ? unrealizedPL.map { $0 / costBasis * 100 } : nil }

    public init(id: String = UUID().uuidString, symbol: String, quantity: Double = 0, averagePrice: Double = 0, currentPrice: Double? = nil, currency: String = "USD") {
        self.id = id; self.symbol = symbol; self.quantity = quantity; self.averagePrice = averagePrice; self.currentPrice = currentPrice; self.currency = currency
    }
}

// MARK: - Portfolio

public struct Portfolio: Sendable, Codable, Identifiable {
    public let id: String
    public var name: String
    public var description: String
    public var holdings: [Holding]
    public var transactions: [Transaction]
    public var cashBalance: Double
    public var currency: String
    public let createdAt: Date
    public var updatedAt: Date

    public init(id: String = UUID().uuidString, name: String, description: String = "", holdings: [Holding] = [], transactions: [Transaction] = [], cashBalance: Double = 0, currency: String = "USD") {
        self.id = id; self.name = name; self.description = description; self.holdings = holdings
        self.transactions = transactions; self.cashBalance = cashBalance; self.currency = currency
        createdAt = Date(); updatedAt = Date()
    }

    public var totalInvested: Double { holdings.reduce(0) { $0 + $1.costBasis } }
    public var totalValue: Double { cashBalance + holdings.compactMap(\.currentValue).reduce(0, +) }
    public var totalReturn: Double { totalValue - totalInvested - cashBalance }
    public var totalReturnPercent: Double { totalInvested > 0 ? totalReturn / totalInvested * 100 : 0 }
}

// MARK: - Watchlist

public struct Watchlist: Sendable, Codable, Identifiable {
    public let id: String
    public var name: String
    public var symbols: [WatchlistItem]
    public let createdAt: Date

    public init(id: String = UUID().uuidString, name: String, symbols: [WatchlistItem] = []) {
        self.id = id; self.name = name; self.symbols = symbols; createdAt = Date()
    }
}

public struct WatchlistItem: Sendable, Codable, Identifiable {
    public let id: String
    public let symbol: String
    public var notes: String
    public var priority: Int
    public var addedAt: Date

    public init(id: String = UUID().uuidString, symbol: String, notes: String = "", priority: Int = 0) {
        self.id = id; self.symbol = symbol; self.notes = notes; self.priority = priority; addedAt = Date()
    }
}

// MARK: - Performance

public struct PerformanceSnapshot: Sendable, Codable {
    public let date: Date
    public let totalValue: Double
    public let dailyReturn: Double
    public let cumulativeReturn: Double
    public let holdingsCount: Int

    public init(date: Date = Date(), totalValue: Double, dailyReturn: Double = 0, cumulativeReturn: Double = 0, holdingsCount: Int = 0) {
        self.date = date; self.totalValue = totalValue; self.dailyReturn = dailyReturn; self.cumulativeReturn = cumulativeReturn; self.holdingsCount = holdingsCount
    }
}

public struct PortfolioSummary: Sendable, Codable {
    public let totalValue: Double; public let totalInvested: Double; public let totalReturn: Double; public let totalReturnPercent: Double
    public let cashBalance: Double; public let holdingsCount: Int; public let dayChange: Double; public let dayChangePercent: Double
    public let topHolding: String?; public let worstHolding: String?

    public init(totalValue: Double, totalInvested: Double, totalReturn: Double, totalReturnPercent: Double, cashBalance: Double, holdingsCount: Int, dayChange: Double, dayChangePercent: Double, topHolding: String?, worstHolding: String?) {
        self.totalValue = totalValue; self.totalInvested = totalInvested; self.totalReturn = totalReturn; self.totalReturnPercent = totalReturnPercent
        self.cashBalance = cashBalance; self.holdingsCount = holdingsCount; self.dayChange = dayChange; self.dayChangePercent = dayChangePercent
        self.topHolding = topHolding; self.worstHolding = worstHolding
    }
}
