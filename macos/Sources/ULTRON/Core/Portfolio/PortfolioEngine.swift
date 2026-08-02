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
    private var restorationTask: Task<Void, Never>?
    private var pendingSave: Task<Void, Never>?
    private var lastSavedFingerprint: Data?

    public init(storage: PortfolioStorage, logger: Logger) {
        self.storage = storage
        self.logger = logger
        restorationTask = Task { @MainActor [weak self] in
            await self?.loadPersistedState()
        }
    }

    /// Waits for the automatic initialization restore to complete.
    public func restorePersistedState() async {
        if let restorationTask {
            await restorationTask.value
            self.restorationTask = nil
        } else {
            await loadPersistedState()
        }
    }

    /// Waits for any queued save to complete. The UI never needs to call this.
    public func flushPersistence() async {
        await restorationTask?.value
        await pendingSave?.value
    }

    // MARK: - Portfolios

    public func createPortfolio(name: String, description: String = "", cash: Double = 0) -> Portfolio {
        let p = Portfolio(name: name, description: description, cashBalance: cash)
        portfolios.append(p)
        scheduleSaveIfChanged()
        return p
    }

    public func getPortfolio(id: String) -> Portfolio? { portfolios.first { $0.id == id } }
    public func getAllPortfolios() -> [Portfolio] { portfolios }
    public func deletePortfolio(id: String) {
        let previousCount = portfolios.count
        portfolios.removeAll { $0.id == id }
        if portfolios.count != previousCount { scheduleSaveIfChanged() }
    }

    public func renamePortfolio(id: String, name: String, description: String? = nil) {
        guard let idx = portfolios.firstIndex(where: { $0.id == id }) else { return }
        portfolios[idx].name = name
        if let description { portfolios[idx].description = description }
        portfolios[idx].updatedAt = Date()
        scheduleSaveIfChanged()
    }

    public func updatePortfolioMetadata(id: String, description: String? = nil, currency: String? = nil) {
        guard let idx = portfolios.firstIndex(where: { $0.id == id }) else { return }
        if let description { portfolios[idx].description = description }
        if let currency { portfolios[idx].currency = currency }
        portfolios[idx].updatedAt = Date()
        scheduleSaveIfChanged()
    }

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
        scheduleSaveIfChanged()
    }

    /// Updates current prices for holdings matching the given quotes.
    public func updatePrices(quotes: [String: Double]) {
        var changed = false
        for i in portfolios.indices {
            for j in portfolios[i].holdings.indices {
                if let price = quotes[portfolios[i].holdings[j].symbol] {
                    if portfolios[i].holdings[j].currentPrice != price {
                        portfolios[i].holdings[j].currentPrice = price
                        changed = true
                    }
                }
            }
            if changed { portfolios[i].updatedAt = Date() }
        }
        if changed { scheduleSaveIfChanged() }
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
        scheduleSaveIfChanged()
        return w
    }

    public func addToWatchlist(watchlistID: String, symbol: String) throws {
        guard let idx = watchlists.firstIndex(where: { $0.id == watchlistID }) else { throw PortfolioError.notFound(watchlistID) }
        guard !watchlists[idx].symbols.contains(where: { $0.symbol == symbol }) else { throw PortfolioError.duplicateSymbol(symbol) }
        watchlists[idx].symbols.append(WatchlistItem(symbol: symbol))
        scheduleSaveIfChanged()
    }

    public func removeFromWatchlist(watchlistID: String, symbol: String) {
        guard let idx = watchlists.firstIndex(where: { $0.id == watchlistID }) else { return }
        let count = watchlists[idx].symbols.count
        watchlists[idx].symbols.removeAll { $0.symbol == symbol }
        if watchlists[idx].symbols.count != count { scheduleSaveIfChanged() }
    }

    public func getWatchlist(id: String) -> Watchlist? { watchlists.first { $0.id == id } }
    public func getAllWatchlists() -> [Watchlist] { watchlists }

    private func loadPersistedState() async {
        guard let envelope: PortfolioPersistenceEnvelope = try? await storage.load(forKey: "portfolio-state") else {
            lastSavedFingerprint = fingerprint(for: PortfolioPersistenceEnvelope(portfolios: portfolios, watchlists: watchlists))
            return
        }
        portfolios = envelope.portfolios
        watchlists = envelope.watchlists
        lastSavedFingerprint = fingerprint(for: envelope)
    }

    private func scheduleSaveIfChanged() {
        let snapshot = PortfolioPersistenceEnvelope(portfolios: portfolios, watchlists: watchlists)
        let currentFingerprint = fingerprint(for: snapshot)
        guard currentFingerprint != lastSavedFingerprint else { return }
        lastSavedFingerprint = currentFingerprint
        let previous = pendingSave
        pendingSave = Task { [storage, logger] in
            await previous?.value
            do {
                try await storage.save(snapshot, forKey: "portfolio-state")
            } catch {
                await logger.error("Portfolio persistence failed", metadata: ["error": String(describing: error)])
            }
        }
    }

    private func fingerprint(for snapshot: PortfolioPersistenceEnvelope) -> Data? {
        try? JSONEncoder().encode(snapshot)
    }
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
