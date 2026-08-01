import Foundation

/// Pure functions for portfolio calculations. Stateless.
public enum PortfolioCalculator {

    /// Calculates the new average buy price after a buy transaction.
    public static func averagePriceAfterBuy(currentQty: Double, currentAvg: Double, buyQty: Double, buyPrice: Double) -> Double {
        let totalCost = currentQty * currentAvg + buyQty * buyPrice
        let totalQty = currentQty + buyQty
        return totalQty > 0 ? totalCost / totalQty : 0
    }

    /// Calculates cost basis after a partial sell.
    public static func costBasisAfterSell(currentQty: Double, currentAvg: Double, sellQty: Double) -> (qty: Double, avg: Double, realizedPL: Double) {
        let remaining = currentQty - sellQty
        return (remaining, remaining > 0 ? currentAvg : 0, sellQty * currentAvg)
    }

    /// Allocation percentage of a holding within total portfolio value.
    public static func allocationPercent(holdingValue: Double, totalValue: Double) -> Double {
        totalValue > 0 ? holdingValue / totalValue * 100 : 0
    }

    /// Cash percentage in portfolio.
    public static func cashPercent(cash: Double, totalValue: Double) -> Double {
        totalValue > 0 ? cash / totalValue * 100 : 0
    }

    /// Simple annualized return.
    public static func annualizedReturn(totalReturn: Double, totalInvested: Double, years: Double) -> Double? {
        guard totalInvested > 0, years > 0 else { return nil }
        return pow((totalInvested + totalReturn) / totalInvested, 1.0 / years) - 1
    }

    /// CAGR from a series of values.
    public static func cagr(startValue: Double, endValue: Double, years: Double) -> Double? {
        guard startValue > 0, years > 0 else { return nil }
        return pow(endValue / startValue, 1.0 / years) - 1
    }

    /// Maximum drawdown from a series of values.
    public static func maxDrawdown(values: [Double]) -> Double {
        guard values.count > 1 else { return 0 }
        var peak = values[0]; var maxDD = 0.0
        for v in values.dropFirst() {
            if v > peak { peak = v } else { maxDD = max(maxDD, (peak - v) / peak) }
        }
        return maxDD * 100
    }

    /// Sharpe ratio (simplified: no risk-free rate).
    public static func sharpeRatio(dailyReturns: [Double]) -> Double? {
        guard dailyReturns.count > 1 else { return nil }
        let mean = dailyReturns.reduce(0, +) / Double(dailyReturns.count)
        let variance = dailyReturns.reduce(0) { $0 + pow($1 - mean, 2) } / Double(dailyReturns.count - 1)
        let stdDev = sqrt(variance)
        return stdDev > 0 ? mean / stdDev * sqrt(252) : nil
    }

    /// Diversification score (lower concentration = higher score, 0-100).
    public static func diversificationScore(holdings: [(symbol: String, value: Double)]) -> Double {
        guard holdings.count > 1 else { return 0 }
        let total = holdings.reduce(0) { $0 + $1.value }
        guard total > 0 else { return 0 }
        let weights = holdings.map { $0.value / total }
        let hhi = weights.reduce(0) { $0 + $1 * $1 }
        let n = Double(holdings.count)
        return max(0, min(100, (1 - hhi) / (1 - 1 / n) * 100))
    }
}
