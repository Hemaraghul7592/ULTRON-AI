import Foundation
import Testing

@testable import ULTRON

// MARK: - Test Data

private func testIS() -> IncomeStatement {
    IncomeStatement(symbol: "AAPL", fiscalYear: 2024, period: .annual,
        revenue: 383_000_000_000, costOfRevenue: 220_000_000_000,
        operatingExpenses: 55_000_000_000, operatingIncome: 108_000_000_000,
        netIncome: 97_000_000_000, eps: 6.50, ebitda: 130_000_000_000,
        sharesOutstanding: 15_000_000_000)
}

private func testBS() -> BalanceSheet {
    BalanceSheet(symbol: "AAPL", fiscalYear: 2024, period: .annual,
        totalAssets: 365_000_000_000, totalLiabilities: 290_000_000_000,
        totalEquity: 75_000_000_000, currentAssets: 145_000_000_000,
        currentLiabilities: 135_000_000_000, longTermDebt: 95_000_000_000,
        cash: 65_000_000_000, inventory: 6_000_000_000,
        receivables: 50_000_000_000, payables: 60_000_000_000,
        bookValuePerShare: 5)
}

private func testCF() -> CashFlowStatement {
    CashFlowStatement(symbol: "AAPL", fiscalYear: 2024, period: .annual,
        operatingCashFlow: 110_000_000_000, capitalExpenditure: 10_000_000_000,
        freeCashFlow: 100_000_000_000)
}

private let testPrice = 190.0

// MARK: - Ratio Calculator Tests

@Suite struct RatioCalculatorTests {
    let stmt = testIS(); let bal = testBS(); let cf = testCF()

    @Test("P/E ratio calculates correctly") func testPE() {
        let pe = RatioCalculator.peRatio(price: testPrice, eps: stmt.eps)
        #expect(pe != nil)
        #expect(abs(pe! - 29.23) < 0.1)
    }

    @Test("P/E returns nil for negative EPS") func testPENegative() {
        #expect(RatioCalculator.peRatio(price: 100, eps: -1) == nil)
    }

    @Test("P/B ratio calculates correctly") func testPB() {
        let pb = RatioCalculator.pbRatio(price: testPrice, bookValuePerShare: bal.bookValuePerShare)
        #expect(pb == 38.0)
    }

    @Test("Gross margin calculates correctly") func testGrossMargin() {
        let gm = RatioCalculator.grossMargin(grossProfit: stmt.grossProfit, revenue: stmt.revenue)
        #expect(gm != nil)
        #expect(abs(gm! - 0.425) < 0.01)
    }

    @Test("Net margin calculates correctly") func testNetMargin() {
        let nm = RatioCalculator.netMargin(netIncome: stmt.netIncome, revenue: stmt.revenue)
        #expect(abs(nm! - 0.253) < 0.01)
    }

    @Test("ROE calculates correctly") func testROE() {
        let roe = RatioCalculator.roe(netIncome: stmt.netIncome, equity: bal.totalEquity)
        #expect(roe! > 1.0)
    }

    @Test("Current ratio calculates correctly") func testCurrentRatio() {
        let cr = RatioCalculator.currentRatio(currentAssets: bal.currentAssets, currentLiabilities: bal.currentLiabilities)
        #expect(abs(cr! - 1.074) < 0.01)
    }

    @Test("Quick ratio is less than current ratio") func testQuickRatio() {
        let cr = RatioCalculator.currentRatio(currentAssets: bal.currentAssets, currentLiabilities: bal.currentLiabilities)!
        let qr = RatioCalculator.quickRatio(currentAssets: bal.currentAssets, inventory: bal.inventory, currentLiabilities: bal.currentLiabilities)!
        #expect(qr < cr)
    }

    @Test("Debt to equity calculates correctly") func testDebtToEquity() {
        let de = RatioCalculator.debtToEquity(totalDebt: bal.longTermDebt, equity: bal.totalEquity)!
        #expect(de > 0)
    }

    @Test("Asset turnover calculates correctly") func testAssetTurnover() {
        let at = RatioCalculator.assetTurnover(revenue: stmt.revenue, totalAssets: bal.totalAssets)!
        #expect(at > 0)
    }

    @Test("Growth rate calculates correctly") func testGrowth() {
        let g = RatioCalculator.growthRate(current: 120, previous: 100)
        #expect(g == 0.2)
    }

    @Test("Growth with zero previous returns nil") func testGrowthZero() {
        #expect(RatioCalculator.growthRate(current: 100, previous: 0) == nil)
    }

    @Test("CAGR calculates correctly") func testCAGR() {
        let cagr = RatioCalculator.cagr(endValue: 200, startValue: 100, years: 5)!
        #expect(abs(cagr - 0.1487) < 0.01)
    }

    @Test("Market cap calculates correctly") func testMarketCap() {
        let mc = RatioCalculator.marketCap(shares: stmt.sharesOutstanding, price: testPrice)
        #expect(mc == 2_850_000_000_000)
    }

    @Test("Enterprise value calculates correctly") func testEV() {
        let mc = RatioCalculator.marketCap(shares: stmt.sharesOutstanding, price: testPrice)
        let ev = RatioCalculator.enterpriseValue(marketCap: mc, debt: bal.longTermDebt, cash: bal.cash)
        #expect(ev == 2_880_000_000_000)
    }

    @Test("Interest coverage calculates correctly") func testInterestCoverage() {
        let ic = RatioCalculator.interestCoverage(operatingIncome: 100, interestExpense: 10)!
        #expect(ic == 10)
    }

    @Test("Interest coverage returns nil for zero interest") func testInterestCoverageNil() {
        #expect(RatioCalculator.interestCoverage(operatingIncome: 100, interestExpense: 0) == nil)
    }
}

// MARK: - Valuation Engine Tests

@Suite struct ValuationEngineTests {
    let stmt = testIS(); let bal = testBS(); let cf = testCF()

    @Test("DCF produces a value") func testDCF() throws {
        let val = try ValuationEngine.dcf(freeCashFlow: cf.freeCashFlow, growthRate: 0.10, terminalGrowth: 0.025, discountRate: 0.10, years: 5, shares: stmt.sharesOutstanding)
        #expect(val != nil)
        #expect(val! > 0)
    }

    @Test("DCF returns nil for negative FCF") func testDCFNegative() throws {
        #expect(try ValuationEngine.dcf(freeCashFlow: -1, growthRate: 0.10, terminalGrowth: 0.025, discountRate: 0.10) == nil)
    }

    @Test("Graham formula produces a value") func testGraham() {
        let val = ValuationEngine.graham(eps: stmt.eps, growthRate: 0.10)
        #expect(val != nil)
        #expect(val! > 0)
    }

    @Test("Graham returns nil for negative EPS") func testGrahamNegative() {
        #expect(ValuationEngine.graham(eps: -1, growthRate: 0.10) == nil)
    }

    @Test("EPV produces a value") func testEPV() {
        let val = ValuationEngine.epv(operatingIncome: stmt.operatingIncome)
        #expect(val != nil)
        #expect(val! > 0)
    }

    @Test("Margin of safety calculates correctly") func testMarginOfSafety() {
        let mos = ValuationEngine.marginOfSafety(intrinsicValue: 150, marketPrice: 100)!
        #expect(abs(mos - 0.333) < 0.01)
    }
}

// MARK: - Fundamental Score Engine Tests

@Suite struct FundamentalScoreEngineTests {
    let stmt = testIS(); let bal = testBS(); let cf = testCF()

    @Test("Score produces rating between 0-100") func testScore() {
        let score = FundamentalScoreEngine.compute(statement: stmt, balance: bal, cashflow: cf, price: testPrice)
        #expect(score.total >= 0)
        #expect(score.total <= 100)
        #expect(!score.components.isEmpty)
    }

    @Test("Profitable company gets good score") func testProfitableScore() {
        let score = FundamentalScoreEngine.compute(statement: stmt, balance: bal, cashflow: cf, price: testPrice)
        #expect(score.rating == .strong || score.rating == .good)
    }

    @Test("Score components add up to total") func testComponentsAddUp() {
        let score = FundamentalScoreEngine.compute(statement: stmt, balance: bal, cashflow: cf, price: testPrice)
        let sum = score.components.values.reduce(0, +)
        #expect(abs(sum - score.total) < 0.01)
    }
}

// MARK: - Fundamental Analysis Engine Tests

@MainActor
@Suite struct FundamentalAnalysisEngineTests {
    let stmt = testIS(); let bal = testBS(); let cf = testCF()
    let engine = FundamentalAnalysisEngine()

    @Test("Valuation analysis produces report") func testValuation() {
        let report = engine.analyzeValuation(statement: stmt, balance: bal, price: testPrice)
        #expect(report.peRatio != nil)
        #expect(report.pbRatio != nil)
        #expect(report.marketCap != nil)
    }

    @Test("Profitability analysis produces report") func testProfitability() {
        let report = engine.analyzeProfitability(stmt)
        #expect(report.grossMargin != nil)
        #expect(report.netMargin != nil)
    }

    @Test("Liquidity analysis produces report") func testLiquidity() {
        let report = engine.analyzeLiquidity(bal)
        #expect(report.currentRatio != nil)
        #expect(report.quickRatio != nil)
    }

    @Test("Leverage analysis produces report") func testLeverage() {
        let report = engine.analyzeLeverage(statement: stmt, balance: bal)
        #expect(report.debtToEquity != nil)
    }

    @Test("Efficiency analysis produces report") func testEfficiency() {
        let report = engine.analyzeEfficiency(statement: stmt, balance: bal)
        #expect(report.assetTurnover != nil)
    }

    @Test("Intrinsic value computes all models") func testIntrinsicValue() {
        let iv = engine.computeIntrinsicValue(statement: stmt, balance: bal, cashflow: cf, price: testPrice)
        #expect(iv.averageValue != nil)
        #expect(iv.marginOfSafety != nil)
    }

    @Test("Full analysis produces all reports") func testFullAnalysis() {
        let result = engine.analyze(statement: stmt, balance: bal, cashflow: cf, price: testPrice)
        #expect(result.score.total >= 0)
        #expect(result.valuation.peRatio != nil)
        #expect(result.profitability.netMargin != nil)
        #expect(result.liquidity.currentRatio != nil)
        #expect(result.leverage.debtToEquity != nil)
        #expect(result.efficiency.assetTurnover != nil)
        #expect(result.intrinsicValue.averageValue != nil)
    }
}

// MARK: - Edge Case Tests

@Suite struct FundamentalEdgeCaseTests {

    @Test("Zero-revenue company handles gracefully") func testZeroRevenue() {
        let stmt = IncomeStatement(symbol: "ZERO", fiscalYear: 2024, period: .annual, revenue: 0, costOfRevenue: 0, operatingExpenses: 10, operatingIncome: -10, netIncome: -10, eps: -1)
        let ratio = RatioCalculator.valuationReport(statement: stmt, balance: BalanceSheet(symbol: "ZERO", fiscalYear: 2024, period: .annual, totalAssets: 100, totalLiabilities: 50, totalEquity: 50, currentAssets: 10, currentLiabilities: 5), price: 10)
        #expect(ratio.peRatio == nil)
        #expect(ratio.psRatio == nil)
    }

    @Test("Negative equity company handles gracefully") func testNegativeEquity() {
        _ = BalanceSheet(symbol: "NEG", fiscalYear: 2024, period: .annual, totalAssets: 100, totalLiabilities: 150, totalEquity: -50, currentAssets: 10, currentLiabilities: 5)
        let de = RatioCalculator.debtToEquity(totalDebt: 50, equity: -50)
        #expect(de == nil)
    }

    @Test("Growth from negative to positive") func testGrowthNegativePositive() {
        let g = RatioCalculator.growthRate(current: 10, previous: -10)
        #expect(g == -2.0)
    }
}
