import Foundation

/// Calculates intrinsic value using multiple valuation models.
public enum ValuationEngine {

    // MARK: - Discounted Cash Flow

    /// DCF valuation: projects FCF for N years, discounts back, adds terminal value.
    public static func dcf(
        freeCashFlow: Double, growthRate: Double, terminalGrowth: Double,
        discountRate: Double, years: Int = 5, shares: Double = 1
    ) throws -> Double? {
        guard freeCashFlow > 0 else { return nil }
        guard discountRate > terminalGrowth else { return nil }

        var pv: Double = 0
        var fcf = freeCashFlow * (1 + growthRate)
        for t in 1...years {
            pv += fcf / pow(1 + discountRate, Double(t))
            fcf *= (1 + growthRate)
        }
        let terminal = fcf * (1 + terminalGrowth) / (discountRate - terminalGrowth)
        pv += terminal / pow(1 + discountRate, Double(years))
        return pv / shares
    }

    // MARK: - Benjamin Graham Formula

    /// V = EPS × (8.5 + 2g) × 4.4 / Y
    public static func graham(eps: Double, growthRate: Double, bondYield: Double = 0.04) -> Double? {
        guard eps > 0 else { return nil }
        return eps * (8.5 + 2 * growthRate * 100) * 4.4 / bondYield
    }

    // MARK: - Earnings Power Value

    /// EPV = Adjusted Earnings / Cost of Capital
    public static func epv(operatingIncome: Double, taxRate: Double = 0.25, costOfCapital: Double = 0.10) -> Double? {
        guard costOfCapital > 0 else { return nil }
        return operatingIncome * (1 - taxRate) / costOfCapital
    }

    // MARK: - Margin of Safety

    public static func marginOfSafety(intrinsicValue: Double, marketPrice: Double) -> Double? {
        guard marketPrice > 0 else { return nil }
        return (intrinsicValue - marketPrice) / intrinsicValue
    }
}
