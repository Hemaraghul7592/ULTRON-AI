import Foundation

/// Evaluates alert conditions against market data.
public enum AlertEvaluator {

    /// Full evaluation with all data sources.
    public static func evaluate(
        _ condition: AlertCondition,
        quotes: [String: Double],
        previousQuotes: [String: Double] = [:],
        portfolioValue: Double? = nil,
        cashBalance: Double? = nil,
        holdingsCount: Int? = nil,
        rsiValues: [String: Double] = [:],
        macdValues: [String: (line: Double, signal: Double)] = [:],
        averageVolume: [String: Int64] = [:],
        currentVolume: [String: Int64] = [:]
    ) -> Alert? {
        switch condition {
        case .priceAbove(let symbol, let threshold):
            guard let price = quotes[symbol], price > threshold else { return nil }
            return Alert(category: .price, severity: .medium, title: "\(symbol) above $\(Int(threshold))", message: "Current: $\(String(format: "%.1f", price))", symbol: symbol, value: price, threshold: threshold)

        case .priceBelow(let symbol, let threshold):
            guard let price = quotes[symbol], price < threshold else { return nil }
            return Alert(category: .price, severity: .medium, title: "\(symbol) below $\(Int(threshold))", message: "Current: $\(String(format: "%.1f", price))", symbol: symbol, value: price, threshold: threshold)

        case .percentGain(let symbol, let percent):
            guard let current = quotes[symbol], let previous = previousQuotes[symbol], previous > 0 else { return nil }
            let change = (current - previous) / previous * 100
            guard change >= percent else { return nil }
            return Alert(category: .price, severity: .medium, title: "\(symbol) gained \(String(format: "%.1f", change))%", message: "From $\(String(format: "%.1f", previous))", symbol: symbol, value: change, threshold: percent)

        case .percentLoss(let symbol, let percent):
            guard let current = quotes[symbol], let previous = previousQuotes[symbol], previous > 0 else { return nil }
            let change = (previous - current) / previous * 100
            guard change >= percent else { return nil }
            return Alert(category: .price, severity: .high, title: "\(symbol) dropped \(String(format: "%.1f", change))%", message: "From $\(String(format: "%.1f", previous))", symbol: symbol, value: change, threshold: percent)

        case .rsiAbove(let symbol, let threshold):
            guard let rsi = rsiValues[symbol], rsi > threshold else { return nil }
            return Alert(category: .technical, severity: .medium, title: "\(symbol) RSI above \(Int(threshold))", message: "RSI: \(String(format: "%.1f", rsi))", symbol: symbol, value: rsi, threshold: threshold)

        case .rsiBelow(let symbol, let threshold):
            guard let rsi = rsiValues[symbol], rsi < threshold else { return nil }
            return Alert(category: .technical, severity: .medium, title: "\(symbol) RSI below \(Int(threshold))", message: "RSI: \(String(format: "%.1f", rsi))", symbol: symbol, value: rsi, threshold: threshold)

        case .macdCrossover(let symbol):
            guard let macd = macdValues[symbol] else { return nil }
            let bullish = macd.line > macd.signal && macd.line > 0
            let bearish = macd.line < macd.signal && macd.line < 0
            if bullish { return Alert(category: .technical, severity: .medium, title: "\(symbol) MACD bullish crossover", message: "Line above signal", symbol: symbol, value: macd.line) }
            if bearish { return Alert(category: .technical, severity: .medium, title: "\(symbol) MACD bearish crossover", message: "Line below signal", symbol: symbol, value: macd.line) }
            return nil

        case .portfolioValueAbove(let threshold):
            guard let value = portfolioValue, value > threshold else { return nil }
            return Alert(category: .portfolio, severity: .medium, title: "Portfolio above $\(Int(threshold))", message: "Value: $\(String(format: "%.0f", value))", value: value, threshold: threshold)

        case .portfolioValueBelow(let threshold):
            guard let value = portfolioValue, value < threshold else { return nil }
            return Alert(category: .portfolio, severity: .high, title: "Portfolio below $\(Int(threshold))", message: "Value: $\(String(format: "%.0f", value))", value: value, threshold: threshold)

        case .portfolioDrawdown:
            guard let value = portfolioValue, value < 0 else { return nil }
            return Alert(category: .portfolio, severity: .high, title: "Portfolio drawdown detected", message: "Portfolio has declined", value: value)

        case .cashBelow(let threshold):
            guard let cash = cashBalance, cash < threshold else { return nil }
            return Alert(category: .portfolio, severity: .low, title: "Cash below $\(Int(threshold))", message: "Cash: $\(String(format: "%.0f", cash))", value: cash, threshold: threshold)

        case .holdingConcentration(let percent):
            guard let count = holdingsCount, count > 0 else { return nil }
            if 100.0 / Double(count) < percent * 0.5 { return Alert(category: .portfolio, severity: .medium, title: "Low diversification", message: "Only \(count) holdings", value: Double(count)) }
            return nil

        case .volumeSpike(let symbol, let multiplier):
            guard let current = currentVolume[symbol], let avg = averageVolume[symbol], avg > 0 else { return nil }
            if Double(current) > Double(avg) * multiplier { return Alert(category: .price, severity: .medium, title: "\(symbol) volume spike", message: "\(current) vs avg \(avg)", symbol: symbol, value: Double(current), threshold: Double(avg) * multiplier) }
            return nil

        case .and(let a, let b):
            guard evaluate(a, quotes: quotes, previousQuotes: previousQuotes, portfolioValue: portfolioValue, cashBalance: cashBalance, holdingsCount: holdingsCount, rsiValues: rsiValues, macdValues: macdValues, averageVolume: averageVolume, currentVolume: currentVolume) != nil else { return nil }
            return evaluate(b, quotes: quotes, previousQuotes: previousQuotes, portfolioValue: portfolioValue, cashBalance: cashBalance, holdingsCount: holdingsCount, rsiValues: rsiValues, macdValues: macdValues, averageVolume: averageVolume, currentVolume: currentVolume)

        case .or(let a, let b):
            return evaluate(a, quotes: quotes, previousQuotes: previousQuotes, portfolioValue: portfolioValue, cashBalance: cashBalance, holdingsCount: holdingsCount, rsiValues: rsiValues, macdValues: macdValues, averageVolume: averageVolume, currentVolume: currentVolume)
                ?? evaluate(b, quotes: quotes, previousQuotes: previousQuotes, portfolioValue: portfolioValue, cashBalance: cashBalance, holdingsCount: holdingsCount, rsiValues: rsiValues, macdValues: macdValues, averageVolume: averageVolume, currentVolume: currentVolume)

        case .not(let inner):
            return evaluate(inner, quotes: quotes, previousQuotes: previousQuotes, portfolioValue: portfolioValue, cashBalance: cashBalance, holdingsCount: holdingsCount, rsiValues: rsiValues, macdValues: macdValues, averageVolume: averageVolume, currentVolume: currentVolume) == nil
                ? Alert(category: .system, severity: .info, title: "NOT condition triggered")
                : nil

        case .alwaysTrue:
            return Alert(category: .system, severity: .info, title: "Always-true condition triggered")
        }
    }
}
