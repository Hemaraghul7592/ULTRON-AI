import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite struct PortfolioEngineTests {

    // MARK: - Creation

    @Test("Create portfolio with name and cash") func testCreatePortfolio() {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "Test", cash: 10000)
        #expect(p.name == "Test")
        #expect(p.cashBalance == 10000)
        #expect(p.holdings.isEmpty)
    }

    @Test("Get portfolio by ID") func testGetPortfolio() {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1")
        let found = engine.getPortfolio(id: p.id)
        #expect(found?.name == "P1")
    }

    @Test("Delete portfolio") func testDeletePortfolio() {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1")
        engine.deletePortfolio(id: p.id)
        #expect(engine.getPortfolio(id: p.id) == nil)
    }

    // MARK: - Buy

    @Test("Buy adds holding with average price") func testBuy() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        let updated = engine.getPortfolio(id: p.id)!
        #expect(updated.holdings.count == 1)
        #expect(updated.holdings[0].symbol == "AAPL")
        #expect(updated.holdings[0].quantity == 10)
        #expect(updated.holdings[0].averagePrice == 150)
        #expect(updated.cashBalance == 8500)
    }

    @Test("Multiple buys average correctly") func testMultipleBuys() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 50000)
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 160))
        let h = engine.getPortfolio(id: p.id)!.holdings[0]
        #expect(h.quantity == 20)
        #expect(abs(h.averagePrice - 155) < 0.01)
    }

    @Test("Buy fails with insufficient cash") func testBuyInsufficientCash() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 100)
        #expect(throws: PortfolioError.self) {
            try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        }
    }

    // MARK: - Sell

    @Test("Sell reduces quantity and adds cash") func testSell() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        try engine.addTransaction(to: p.id, Transaction(type: .sell, symbol: "AAPL", quantity: 5, price: 160))

        let updated = engine.getPortfolio(id: p.id)!
        #expect(updated.holdings[0].quantity == 5)
        #expect(updated.cashBalance == 9300)
    }

    @Test("Sell all removes holding") func testSellAll() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        try engine.addTransaction(to: p.id, Transaction(type: .sell, symbol: "AAPL", quantity: 10, price: 160))
        #expect(engine.getPortfolio(id: p.id)!.holdings.isEmpty)
    }

    @Test("Sell insufficient holdings throws") func testSellInsufficient() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        #expect(throws: PortfolioError.self) {
            try engine.addTransaction(to: p.id, Transaction(type: .sell, symbol: "AAPL", quantity: 5, price: 150))
        }
    }

    // MARK: - Deposit/Withdrawal

    @Test("Deposit increases cash") func testDeposit() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 1000)
        try engine.addTransaction(to: p.id, Transaction(type: .deposit, symbol: "CASH", quantity: 1, price: 500))
        #expect(engine.getPortfolio(id: p.id)!.cashBalance == 1500)
    }

    @Test("Withdrawal decreases cash") func testWithdrawal() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 1000)
        try engine.addTransaction(to: p.id, Transaction(type: .withdrawal, symbol: "CASH", quantity: 1, price: 300))
        #expect(engine.getPortfolio(id: p.id)!.cashBalance == 700)
    }

    @Test("Withdrawal insufficient throws") func testWithdrawalInsufficient() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 100)
        #expect(throws: PortfolioError.self) {
            try engine.addTransaction(to: p.id, Transaction(type: .withdrawal, symbol: "CASH", quantity: 1, price: 200))
        }
    }

    // MARK: - Prices

    @Test("Update prices reflects current values") func testUpdatePrices() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        engine.updatePrices(quotes: ["AAPL": 180])

        let h = engine.getPortfolio(id: p.id)!.holdings[0]
        #expect(h.currentPrice == 180)
        #expect(h.currentValue == 1800)
        #expect(h.unrealizedPL == 300)
    }

    // MARK: - Summary

    @Test("Summary reflects portfolio state") func testSummary() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "GOOGL", quantity: 5, price: 140))
        engine.updatePrices(quotes: ["AAPL": 180, "GOOGL": 130])

        let s = engine.summary(for: p.id)!
        #expect(s.holdingsCount == 2)
        #expect(s.cashBalance == 7800)
        #expect(s.topHolding == "AAPL")
        #expect(s.worstHolding == "GOOGL")
    }

    // MARK: - Watchlist

    @Test("Create and add to watchlist") func testWatchlist() throws {
        let engine = makeEngine()
        let w = engine.createWatchlist(name: "Tech")
        try engine.addToWatchlist(watchlistID: w.id, symbol: "AAPL")
        try engine.addToWatchlist(watchlistID: w.id, symbol: "GOOGL")

        let found = engine.getWatchlist(id: w.id)!
        #expect(found.symbols.count == 2)
    }

    @Test("Watchlist prevents duplicates") func testWatchlistDuplicate() throws {
        let engine = makeEngine()
        let w = engine.createWatchlist(name: "Tech")
        try engine.addToWatchlist(watchlistID: w.id, symbol: "AAPL")
        #expect(throws: PortfolioError.self) {
            try engine.addToWatchlist(watchlistID: w.id, symbol: "AAPL")
        }
    }

    @Test("Remove from watchlist") func testWatchlistRemove() throws {
        let engine = makeEngine()
        let w = engine.createWatchlist(name: "Tech")
        try engine.addToWatchlist(watchlistID: w.id, symbol: "AAPL")
        engine.removeFromWatchlist(watchlistID: w.id, symbol: "AAPL")
        #expect(engine.getWatchlist(id: w.id)!.symbols.isEmpty)
    }

    // MARK: - Calculator

    @Test("Average price calculation") func testAveragePrice() {
        let avg = PortfolioCalculator.averagePriceAfterBuy(currentQty: 10, currentAvg: 150, buyQty: 10, buyPrice: 160)
        #expect(abs(avg - 155) < 0.01)
    }

    @Test("Sell cost basis") func testSellCostBasis() {
        let (qty, avg, pl) = PortfolioCalculator.costBasisAfterSell(currentQty: 10, currentAvg: 150, sellQty: 4)
        #expect(qty == 6)
        #expect(avg == 150)
        #expect(pl == 600)
    }

    @Test("Allocation percent") func testAllocation() {
        #expect(abs(PortfolioCalculator.allocationPercent(holdingValue: 5000, totalValue: 20000) - 25) < 0.01)
    }

    @Test("CAGR calculation") func testCAGR() {
        let cagr = PortfolioCalculator.cagr(startValue: 10000, endValue: 16105, years: 5)
        #expect(cagr != nil)
        #expect(abs(cagr! - 0.10) < 0.01)
    }

    @Test("Max drawdown") func testMaxDrawdown() {
        let dd = PortfolioCalculator.maxDrawdown(values: [100, 120, 90, 80, 110])
        #expect(abs(dd - 33.33) < 0.5)
    }

    @Test("Diversification score for single holding is low") func testDiversification() {
        let score = PortfolioCalculator.diversificationScore(holdings: [("A", 100)])
        #expect(score == 0)
    }

    @Test("Diversification score for multiple holdings") func testDiversificationMultiple() {
        let score = PortfolioCalculator.diversificationScore(holdings: [("A", 50), ("B", 50)])
        #expect(score > 0)
    }

    @Test("Annualized return") func testAnnualizedReturn() {
        let r = PortfolioCalculator.annualizedReturn(totalReturn: 5000, totalInvested: 10000, years: 3)
        #expect(r != nil)
    }

    // MARK: - Helpers

    @Test("Cannot buy zero quantity") func testBuyZeroQuantity() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        #expect(throws: PortfolioError.self) {
            try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 0, price: 150))
        }
    }

    @Test("Cannot buy negative price") func testBuyNegativePrice() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        #expect(throws: PortfolioError.self) {
            try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: -1))
        }
    }

    @Test("Sell entire position removes holding") func testSellEntire() throws {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        try engine.addTransaction(to: p.id, Transaction(type: .buy, symbol: "AAPL", quantity: 10, price: 150))
        try engine.addTransaction(to: p.id, Transaction(type: .sell, symbol: "AAPL", quantity: 10, price: 160))
        #expect(engine.getPortfolio(id: p.id)!.holdings.isEmpty)
    }

    @Test("Update prices with empty quotes is no-op") func testUpdateEmpty() {
        let engine = makeEngine()
        let p = engine.createPortfolio(name: "P1", cash: 10000)
        engine.updatePrices(quotes: [:])
        #expect(engine.getPortfolio(id: p.id)!.holdings.isEmpty)
    }

    private func makeEngine() -> PortfolioEngine {
        PortfolioEngine(storage: InMemoryStorage(), logger: Logger(configuration: .init(minimumLevel: .error)))
    }
}
