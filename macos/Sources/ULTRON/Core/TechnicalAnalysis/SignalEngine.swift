import Foundation

/// Generates buy/sell signals from indicator and pattern analysis.
///
/// `SignalEngine` combines multiple indicators to produce a consensus
/// signal with confidence scoring. Individual indicator signals are
/// weighted and aggregated.
public enum SignalEngine {

    /// Generates a signal from RSI values.
    public static func rsiSignal(_ rsi: Double) -> TASignal.Strength {
        if rsi > 70 { return .sell }
        if rsi < 30 { return .buy }
        return .neutral
    }

    /// Generates a signal from MACD crossover.
    public static func macdSignal(macd: Double, signal: Double) -> TASignal.Strength {
        if macd > signal && macd > 0 { return .buy }
        if macd < signal && macd < 0 { return .sell }
        return .neutral
    }

    /// Generates a signal from Bollinger Band position.
    public static func bollingerSignal(price: Double, upper: Double, lower: Double) -> TASignal.Strength {
        if price <= lower { return .buy }
        if price >= upper { return .sell }
        return .neutral
    }

    /// Generates a signal from Stochastic oscillator.
    public static func stochasticSignal(k: Double, d: Double) -> TASignal.Strength {
        if k < 20 && d < 20 && k > d { return .buy }
        if k > 80 && d > 80 && k < d { return .sell }
        return .neutral
    }

    /// Combines multiple signal strengths into a weighted consensus.
    /// Weights: RSI=0.25, MACD=0.35, BB=0.25, Stoch=0.15
    public static func consensus(
        rsiStrength: TASignal.Strength,
        macdStrength: TASignal.Strength?,
        bbStrength: TASignal.Strength?,
        stochStrength: TASignal.Strength?
    ) -> TASignal {
        var score = 0.0
        var reasons: [String] = []

        func add(_ s: TASignal.Strength, weight: Double, label: String) {
            switch s {
            case .strongBuy: score += 2 * weight; reasons.append("\(label): Strong Buy")
            case .buy: score += 1 * weight; reasons.append("\(label): Buy")
            case .strongSell: score -= 2 * weight; reasons.append("\(label): Strong Sell")
            case .sell: score -= 1 * weight; reasons.append("\(label): Sell")
            case .neutral: break
            }
        }

        add(rsiStrength, weight: 0.25, label: "RSI")
        if let s = macdStrength { add(s, weight: 0.35, label: "MACD") }
        if let s = bbStrength { add(s, weight: 0.25, label: "Bollinger") }
        if let s = stochStrength { add(s, weight: 0.15, label: "Stochastic") }

        let strength: TASignal.Strength
        if score > 0.8 { strength = .strongBuy }
        else if score > 0.2 { strength = .buy }
        else if score < -0.8 { strength = .strongSell }
        else if score < -0.2 { strength = .sell }
        else { strength = .neutral }

        return TASignal(strength: strength, confidence: min(1, abs(score) / 1.2), reasons: reasons)
    }
}
