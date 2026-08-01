import Foundation

/// Stateless calculator for all financial ratios and metrics.
public enum RatioCalculator {

    // MARK: - Valuation Ratios

    public static func peRatio(price: Double, eps: Double) -> Double? { eps > 0 ? price / eps : nil }
    public static func pbRatio(price: Double, bookValuePerShare: Double) -> Double? { bookValuePerShare > 0 ? price / bookValuePerShare : nil }
    public static func psRatio(marketCap: Double, revenue: Double) -> Double? { revenue > 0 ? marketCap / revenue : nil }
    public static func evToEBITDA(ev: Double, ebitda: Double) -> Double? { ebitda > 0 ? ev / ebitda : nil }
    public static func dividendYield(dividendPerShare: Double, price: Double) -> Double? { price > 0 ? dividendPerShare / price : nil }
    public static func marketCap(shares: Double, price: Double) -> Double { shares * price }
    public static func enterpriseValue(marketCap: Double, debt: Double, cash: Double) -> Double { marketCap + debt - cash }

    // MARK: - Profitability

    public static func grossMargin(grossProfit: Double, revenue: Double) -> Double? { revenue > 0 ? grossProfit / revenue : nil }
    public static func operatingMargin(operatingIncome: Double, revenue: Double) -> Double? { revenue > 0 ? operatingIncome / revenue : nil }
    public static func netMargin(netIncome: Double, revenue: Double) -> Double? { revenue > 0 ? netIncome / revenue : nil }
    public static func roe(netIncome: Double, equity: Double) -> Double? { equity > 0 ? netIncome / equity : nil }
    public static func roa(netIncome: Double, totalAssets: Double) -> Double? { totalAssets > 0 ? netIncome / totalAssets : nil }

    // MARK: - Liquidity

    public static func currentRatio(currentAssets: Double, currentLiabilities: Double) -> Double? { currentLiabilities > 0 ? currentAssets / currentLiabilities : nil }
    public static func quickRatio(currentAssets: Double, inventory: Double, currentLiabilities: Double) -> Double? { currentLiabilities > 0 ? (currentAssets - inventory) / currentLiabilities : nil }

    // MARK: - Leverage

    public static func debtToEquity(totalDebt: Double, equity: Double) -> Double? { equity > 0 ? totalDebt / equity : nil }
    public static func debtRatio(totalLiabilities: Double, totalAssets: Double) -> Double? { totalAssets > 0 ? totalLiabilities / totalAssets : nil }
    public static func interestCoverage(operatingIncome: Double, interestExpense: Double) -> Double? { interestExpense > 0 ? operatingIncome / interestExpense : nil }

    // MARK: - Efficiency

    public static func assetTurnover(revenue: Double, totalAssets: Double) -> Double? { totalAssets > 0 ? revenue / totalAssets : nil }

    // MARK: - Growth

    public static func growthRate(current: Double, previous: Double) -> Double? { previous != 0 ? (current - previous) / previous : nil }
    public static func cagr(endValue: Double, startValue: Double, years: Double) -> Double? { startValue > 0 && years > 0 ? pow(endValue / startValue, 1.0 / years) - 1 : nil }

    // MARK: - Full Reports

    public static func valuationReport(statement: IncomeStatement, balance: BalanceSheet, price: Double,
                                        forwardEPS: Double? = nil, growthRate: Double? = nil) -> RatioReport {
        let mc = marketCap(shares: statement.sharesOutstanding, price: price)
        let ev = enterpriseValue(marketCap: mc, debt: balance.longTermDebt, cash: balance.cash)
        return RatioReport(symbol: statement.symbol, fiscalYear: statement.fiscalYear,
            peRatio: peRatio(price: price, eps: statement.eps),
            pbRatio: pbRatio(price: price, bookValuePerShare: balance.bookValuePerShare),
            psRatio: psRatio(marketCap: mc, revenue: statement.revenue),
            evToEBITDA: evToEBITDA(ev: ev, ebitda: statement.ebitda),
            marketCap: mc)
    }

    public static func profitabilityReport(_ statement: IncomeStatement) -> ProfitabilityReport {
        ProfitabilityReport(
            grossMargin: grossMargin(grossProfit: statement.grossProfit, revenue: statement.revenue),
            operatingMargin: operatingMargin(operatingIncome: statement.operatingIncome, revenue: statement.revenue),
            netMargin: netMargin(netIncome: statement.netIncome, revenue: statement.revenue))
    }

    public static func liquidityReport(_ balance: BalanceSheet) -> LiquidityReport {
        LiquidityReport(
            currentRatio: currentRatio(currentAssets: balance.currentAssets, currentLiabilities: balance.currentLiabilities),
            quickRatio: quickRatio(currentAssets: balance.currentAssets, inventory: balance.inventory, currentLiabilities: balance.currentLiabilities))
    }

    public static func leverageReport(statement: IncomeStatement, balance: BalanceSheet) -> LeverageReport {
        LeverageReport(
            debtToEquity: debtToEquity(totalDebt: balance.longTermDebt, equity: balance.totalEquity),
            debtRatio: debtRatio(totalLiabilities: balance.totalLiabilities, totalAssets: balance.totalAssets),
            interestCoverage: interestCoverage(operatingIncome: statement.operatingIncome, interestExpense: statement.interestExpense))
    }

    public static func efficiencyReport(statement: IncomeStatement, balance: BalanceSheet) -> EfficiencyReport {
        EfficiencyReport(assetTurnover: assetTurnover(revenue: statement.revenue, totalAssets: balance.totalAssets))
    }
}

// MARK: - Growth Analyzer

public enum GrowthAnalyzer {
    public static func report(current: IncomeStatement, previous: IncomeStatement,
                               currentCF: CashFlowStatement, previousCF: CashFlowStatement) -> GrowthReport {
        GrowthReport(
            revenueGrowth: RatioCalculator.growthRate(current: current.revenue, previous: previous.revenue),
            epsGrowth: RatioCalculator.growthRate(current: current.eps, previous: previous.eps),
            netIncomeGrowth: RatioCalculator.growthRate(current: current.netIncome, previous: previous.netIncome),
            fcfGrowth: RatioCalculator.growthRate(current: currentCF.freeCashFlow, previous: previousCF.freeCashFlow))
    }
}
