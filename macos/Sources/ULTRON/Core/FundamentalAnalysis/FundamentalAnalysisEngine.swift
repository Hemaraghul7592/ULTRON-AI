import Foundation

/// The central entry point for fundamental analysis in ULTRON.
@MainActor
public final class FundamentalAnalysisEngine {

    public let config: FAConfig

    public init(config: FAConfig = .default) {
        self.config = config
    }

    /// Computes all valuation ratios.
    public func analyzeValuation(statement: IncomeStatement, balance: BalanceSheet, price: Double,
                                  forwardEPS: Double? = nil, growthRate: Double? = nil) -> RatioReport {
        RatioCalculator.valuationReport(statement: statement, balance: balance, price: price, forwardEPS: forwardEPS, growthRate: growthRate)
    }

    /// Computes profitability metrics.
    public func analyzeProfitability(_ statement: IncomeStatement) -> ProfitabilityReport {
        RatioCalculator.profitabilityReport(statement)
    }

    /// Computes liquidity metrics.
    public func analyzeLiquidity(_ balance: BalanceSheet) -> LiquidityReport {
        RatioCalculator.liquidityReport(balance)
    }

    /// Computes leverage metrics.
    public func analyzeLeverage(statement: IncomeStatement, balance: BalanceSheet) -> LeverageReport {
        RatioCalculator.leverageReport(statement: statement, balance: balance)
    }

    /// Computes efficiency metrics.
    public func analyzeEfficiency(statement: IncomeStatement, balance: BalanceSheet) -> EfficiencyReport {
        RatioCalculator.efficiencyReport(statement: statement, balance: balance)
    }

    /// Computes growth metrics.
    public func analyzeGrowth(current: IncomeStatement, previous: IncomeStatement, currentCF: CashFlowStatement, previousCF: CashFlowStatement) -> GrowthReport {
        GrowthAnalyzer.report(current: current, previous: previous, currentCF: currentCF, previousCF: previousCF)
    }

    /// Computes intrinsic value.
    public func computeIntrinsicValue(
        statement: IncomeStatement, balance: BalanceSheet, cashflow: CashFlowStatement,
        price: Double, growthRate: Double = 0.10
    ) -> ValuationResult {
        let dcfVal = try? ValuationEngine.dcf(
            freeCashFlow: cashflow.freeCashFlow, growthRate: growthRate,
            terminalGrowth: config.terminalGrowthRate, discountRate: config.defaultDiscountRate,
            years: config.projectionYears, shares: statement.sharesOutstanding)
        let grahamVal = ValuationEngine.graham(eps: statement.eps, growthRate: growthRate, bondYield: config.riskFreeRate)
        let epvVal = ValuationEngine.epv(operatingIncome: statement.operatingIncome, costOfCapital: config.defaultDiscountRate)

        let vals = [dcfVal, grahamVal, epvVal].compactMap { $0 }
        let avg = vals.isEmpty ? nil : vals.reduce(0, +) / Double(vals.count)
        let mos = avg.flatMap { ValuationEngine.marginOfSafety(intrinsicValue: $0, marketPrice: price) }
        return ValuationResult(dcfValue: dcfVal, grahamValue: grahamVal, epvValue: epvVal, averageValue: avg, marginOfSafety: mos)
    }

    /// Full analysis producing all reports.
    public func analyze(
        statement: IncomeStatement, balance: BalanceSheet, cashflow: CashFlowStatement,
        price: Double, growth: GrowthReport? = nil
    ) -> (
        score: FundamentalScore, valuation: RatioReport, profitability: ProfitabilityReport,
        liquidity: LiquidityReport, leverage: LeverageReport, efficiency: EfficiencyReport,
        intrinsicValue: ValuationResult
    ) {
        let score = FundamentalScoreEngine.compute(statement: statement, balance: balance, cashflow: cashflow, price: price, growth: growth)
        let valuation = analyzeValuation(statement: statement, balance: balance, price: price)
        let profitability = analyzeProfitability(statement)
        let liquidity = analyzeLiquidity(balance)
        let leverage = analyzeLeverage(statement: statement, balance: balance)
        let efficiency = analyzeEfficiency(statement: statement, balance: balance)
        let iv = computeIntrinsicValue(statement: statement, balance: balance, cashflow: cashflow, price: price)
        return (score, valuation, profitability, liquidity, leverage, efficiency, iv)
    }
}
