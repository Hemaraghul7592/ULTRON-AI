import Foundation

/// The central entry point for portfolio management in ULTRON.
///
/// Manages portfolios, holdings, transactions, watchlists, and
/// performance tracking. All data is persisted via `PortfolioStorage`.
@MainActor
public final class PortfolioEngine {

    private var portfolios: [Portfolio] = []
    private var watchlists: [Watchlist] = []
    private let storage: PortfolioStorage
    private let logger: Logger

    public init(storage: PortfolioStorage, logger: Logger) {
        self.storage = storage
        self.logger = logger
    }

    // MARK: - Portfolios

    public func createPortfolio(name: String, description: String = "", cash: Double = 0) -> Portfolio {
        let p = Portfolio(name: name, description: description, cashBalance: cash)
        portfolios.append(p)
        return p
    }

    public func getPortfolio(id: String) -> Portfolio? { portfolios.first { $0.id == id } }
    public func getAllPortfolios() -> [Portfolio] { portfolios }
    public func deletePortfolio(id: String) { portfolios.removeAll { $0.id == id } }

    // MARK: - Transactions

    public func addTransaction(to portfolioID: String, _ txn: Transaction) throws {
        guard txn.quantity > 0 else { throw PortfolioError.invalidOperation("Quantity must be positive") }
        guard txn.price > 0 else { throw PortfolioError.invalidOperation("Price must be positive") }

        guard let idx = portfolios.firstIndex(where: { $0.id == portfolioID }) else {
            throw PortfolioError.notFound(portfolioID)
        }
        var p = portfolios[idx]

        switch txn.type {
        case .buy:
            let cost = txn.totalValue
            guard p.cashBalance >= cost else { throw PortfolioError.insufficientCash(required: cost, available: p.cashBalance) }
            p.cashBalance -= cost
            if let hIdx = p.holdings.firstIndex(where: { $0.symbol == txn.symbol }) {
                var h = p.holdings[hIdx]
                h.averagePrice = PortfolioCalculator.averagePriceAfterBuy(currentQty: h.quantity, currentAvg: h.averagePrice, buyQty: txn.quantity, buyPrice: txn.price)
                h.quantity += txn.quantity
                p.holdings[hIdx] = h
            } else {
                p.holdings.append(Holding(symbol: txn.symbol, quantity: txn.quantity, averagePrice: txn.price))
            }

        case .sell:
            guard let hIdx = p.holdings.firstIndex(where: { $0.symbol == txn.symbol }) else {
                throw PortfolioError.insufficientHoldings(symbol: txn.symbol, required: txn.quantity, available: 0)
            }
            var h = p.holdings[hIdx]
            guard h.quantity >= txn.quantity else { throw PortfolioError.insufficientHoldings(symbol: txn.symbol, required: txn.quantity, available: h.quantity) }
            let (qty, avg, _) = PortfolioCalculator.costBasisAfterSell(currentQty: h.quantity, currentAvg: h.averagePrice, sellQty: txn.quantity)
            h.quantity = qty; h.averagePrice = avg
            if h.quantity <= 0 { p.holdings.remove(at: hIdx) } else { p.holdings[hIdx] = h }
            p.cashBalance += txn.totalValue

        case .deposit:
            p.cashBalance += txn.totalValue
        case .withdrawal:
            guard p.cashBalance >= txn.totalValue else { throw PortfolioError.insufficientCash(required: txn.totalValue, available: p.cashBalance) }
            p.cashBalance -= txn.totalValue
        default:
            break
        }

        p.transactions.append(txn)
        p.updatedAt = Date()
        portfolios[idx] = p
    }

    /// Updates current prices for holdings matching the given quotes.
    public func updatePrices(quotes: [String: Double]) {
        for i in portfolios.indices {
            for j in portfolios[i].holdings.indices {
                if let price = quotes[portfolios[i].holdings[j].symbol] {
                    portfolios[i].holdings[j].currentPrice = price
                }
            }
            portfolios[i].updatedAt = Date()
        }
    }

    // MARK: - Summary

    public func summary(for portfolioID: String) -> PortfolioSummary? {
        guard let p = getPortfolio(id: portfolioID) else { return nil }
        var best: (String, Double)?, worst: (String, Double)?
        for h in p.holdings {
            guard let pl = h.unrealizedPLPercent else { continue }
            if best == nil || pl > best!.1 { best = (h.symbol, pl) }
            if worst == nil || pl < worst!.1 { worst = (h.symbol, pl) }
        }
        return PortfolioSummary(
            totalValue: p.totalValue, totalInvested: p.totalInvested, totalReturn: p.totalReturn,
            totalReturnPercent: p.totalReturnPercent, cashBalance: p.cashBalance,
            holdingsCount: p.holdings.count, dayChange: 0, dayChangePercent: 0,
            topHolding: best?.0, worstHolding: worst?.0)
    }

    // MARK: - Watchlists

    public func createWatchlist(name: String) -> Watchlist {
        let w = Watchlist(name: name)
        watchlists.append(w)
        return w
    }

    public func addToWatchlist(watchlistID: String, symbol: String) throws {
        guard let idx = watchlists.firstIndex(where: { $0.id == watchlistID }) else { throw PortfolioError.notFound(watchlistID) }
        guard !watchlists[idx].symbols.contains(where: { $0.symbol == symbol }) else { throw PortfolioError.duplicateSymbol(symbol) }
        watchlists[idx].symbols.append(WatchlistItem(symbol: symbol))
    }

    public func removeFromWatchlist(watchlistID: String, symbol: String) {
        guard let idx = watchlists.firstIndex(where: { $0.id == watchlistID }) else { return }
        watchlists[idx].symbols.removeAll { $0.symbol == symbol }
    }

    public func getWatchlist(id: String) -> Watchlist? { watchlists.first { $0.id == id } }
    public func getAllWatchlists() -> [Watchlist] { watchlists }
}

// MARK: - Storage Protocol

public protocol PortfolioStorage: Sendable {
    func save<T: Codable & Sendable>(_ item: T, forKey key: String) async throws
    func load<T: Codable & Sendable>(forKey key: String) async throws -> T?
    func remove(forKey key: String) async
}

/// In-memory storage for testing and development.
public actor InMemoryStorage: PortfolioStorage {
    public init() {}
    private var data: [String: any Sendable] = [:]

    public func save<T: Codable & Sendable>(_ item: T, forKey key: String) async throws { data[key] = item }
    public func load<T: Codable & Sendable>(forKey key: String) async throws -> T? { data[key] as? T }
    public func remove(forKey key: String) async { data[key] = nil }
}
