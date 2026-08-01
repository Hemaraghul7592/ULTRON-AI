import Foundation

/// Computes a composite fundamental health score from 0-100.
public enum FundamentalScoreEngine {

    public static func compute(
        statement: IncomeStatement, balance: BalanceSheet,
        cashflow: CashFlowStatement, price: Double,
        growth: GrowthReport? = nil
    ) -> FundamentalScore {
        var components: [String: Double] = [:]
        let maxPerCategory = 1.0

        let nm = RatioCalculator.netMargin(netIncome: statement.netIncome, revenue: statement.revenue) ?? 0
        components["profitability"] = clamp(nm * 100, ceiling: maxPerCategory) * 30
        if let roe = RatioCalculator.roe(netIncome: statement.netIncome, equity: balance.totalEquity) {
            components["roe"] = clamp(roe, ceiling: maxPerCategory) * 10
        }

        let cr = RatioCalculator.currentRatio(currentAssets: balance.currentAssets, currentLiabilities: balance.currentLiabilities) ?? 0
        components["liquidity"] = clamp(cr / 2.0, ceiling: maxPerCategory) * 15

        let de = RatioCalculator.debtToEquity(totalDebt: balance.longTermDebt, equity: balance.totalEquity) ?? 1
        components["leverage"] = clamp(1.0 - de, ceiling: maxPerCategory) * 15

        let revGrowth = growth?.revenueGrowth ?? 0
        components["growth"] = clamp(revGrowth * 100, ceiling: maxPerCategory) * 20

        let pe = RatioCalculator.peRatio(price: price, eps: statement.eps) ?? 50
        components["valuation"] = clamp(20.0 / Swift.max(pe, 1), ceiling: maxPerCategory) * 20

        let total = components.values.reduce(0, +)
        return FundamentalScore(total: total, components: components)
    }

    private static func clamp(_ value: Double, ceiling: Double) -> Double {
        min(Swift.max(0, value), ceiling)
    }
}
