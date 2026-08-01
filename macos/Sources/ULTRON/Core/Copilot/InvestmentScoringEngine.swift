import Foundation

/// Computes multi-factor investment scores from existing engine outputs.
public enum InvestmentScoringEngine {

    /// Technical score from RSI (50 is optimal), MACD, and trend.
    public static func technicalScore(rsi: Double?, macdBullish: Bool, aboveMA: Bool) -> Double {
        var score = 50.0
        if let rsi {
            if rsi > 70 { score -= 15 }; if rsi < 30 { score += 10 }
            score += min(10, max(-10, (50 - abs(rsi - 50)) * 0.5))
        }
        if macdBullish { score += 10 }; if aboveMA { score += 10 }
        return max(0, min(100, score))
    }

    /// Fundamental score from growth, margins, and health.
    public static func fundamentalScore(revenueGrowth: Double?, netMargin: Double?, healthScore: Double?) -> Double {
        var score = 50.0
        if let g = revenueGrowth { score += min(20, max(-20, g * 100)) }
        if let m = netMargin { score += min(15, max(-15, (m - 0.10) * 200)) }
        if let h = healthScore { score += (h - 50) * 0.3 }
        return max(0, min(100, score))
    }

    /// Risk score — lower is better (inverted for overall score).
    public static func riskScore(volatility: Double?, drawdown: Double?) -> Double {
        var score = 50.0
        if let v = volatility { score -= min(30, v * 200) }
        if let d = drawdown { score -= min(30, d * 2) }
        return max(0, min(100, score))
    }

    /// Momentum score from price change and volume.
    public static func momentumScore(priceChange: Double?, volumeRatio: Double?) -> Double {
        var score = 50.0
        if let pc = priceChange { score += min(25, max(-25, pc * 200)) }
        if let vr = volumeRatio { score += min(15, max(-15, (vr - 1) * 30)) }
        return max(0, min(100, score))
    }

    /// Valuation score — lower P/E and P/B are better.
    public static func valuationScore(pe: Double?, pb: Double?) -> Double {
        var score = 50.0
        if let pe { score += min(25, max(-25, (20 - pe) * 2.5)) }
        if let pb { score += min(15, max(-15, (3 - pb) * 10)) }
        return max(0, min(100, score))
    }

    /// SEBI governance score from promoter activity and filings.
    public static func sebiGovernanceScore(promoterBuying: Bool, recentFilings: Int, hasInsiderTrading: Bool) -> Double {
        var score = 50.0
        if promoterBuying { score += 20 }; if hasInsiderTrading { score -= 25 }
        score += min(10, Double(recentFilings) * 3)
        return max(0, min(100, score))
    }

    /// Combined score from all factors.
    public static func overallScore(symbol: String, rsi: Double? = nil, macdBullish: Bool = false, aboveMA: Bool = false,
                                     revenueGrowth: Double? = nil, netMargin: Double? = nil, healthScore: Double? = nil,
                                     volatility: Double? = nil, drawdown: Double? = nil, priceChange: Double? = nil,
                                     volumeRatio: Double? = nil, pe: Double? = nil, pb: Double? = nil,
                                     promoterBuying: Bool = false, recentFilings: Int = 0, hasInsiderTrading: Bool = false) -> InvestmentScore {
        InvestmentScore(symbol: symbol,
            technical: technicalScore(rsi: rsi, macdBullish: macdBullish, aboveMA: aboveMA),
            fundamental: fundamentalScore(revenueGrowth: revenueGrowth, netMargin: netMargin, healthScore: healthScore),
            risk: riskScore(volatility: volatility, drawdown: drawdown),
            momentum: momentumScore(priceChange: priceChange, volumeRatio: volumeRatio),
            valuation: valuationScore(pe: pe, pb: pb),
            sentiment: sebiGovernanceScore(promoterBuying: promoterBuying, recentFilings: recentFilings, hasInsiderTrading: hasInsiderTrading))
    }
}
