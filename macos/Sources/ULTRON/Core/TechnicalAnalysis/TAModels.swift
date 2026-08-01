import Foundation

// MARK: - Signal

/// A trading signal generated from indicator and pattern analysis.
public struct TASignal: Sendable, Codable {
    public enum Strength: String, Sendable, Codable, Comparable {
        case strongBuy, buy, neutral, sell, strongSell
        public static func < (lhs: Strength, rhs: Strength) -> Bool {
            let order: [Strength] = [.strongSell, .sell, .neutral, .buy, .strongBuy]
            return (order.firstIndex(of: lhs) ?? 0) < (order.firstIndex(of: rhs) ?? 0)
        }
    }

    public let strength: Strength
    public let confidence: Double
    public let reasons: [String]
    public let symbol: String
    public let timestamp: Date

    public init(strength: Strength, confidence: Double, reasons: [String] = [], symbol: String = "", timestamp: Date = Date()) {
        self.strength = strength; self.confidence = min(1, max(0, confidence))
        self.reasons = reasons; self.symbol = symbol; self.timestamp = timestamp
    }

    public static func neutral(symbol: String = "") -> TASignal {
        TASignal(strength: .neutral, confidence: 0, symbol: symbol)
    }
}

// MARK: - Indicator Results

public struct IndicatorValue: Sendable, Codable {
    public let timestamp: Date
    public let value: Double
    public init(timestamp: Date, value: Double) { self.timestamp = timestamp; self.value = value }
}

public struct SMA: Sendable, Codable {
    public let period: Int; public let values: [IndicatorValue]
    public init(period: Int, values: [IndicatorValue]) { self.period = period; self.values = values }
}

public struct EMA: Sendable, Codable {
    public let period: Int; public let values: [IndicatorValue]
    public init(period: Int, values: [IndicatorValue]) { self.period = period; self.values = values }
}

public struct MACDResult: Sendable, Codable {
    public let macdLine: [IndicatorValue]; public let signalLine: [IndicatorValue]
    public let histogram: [IndicatorValue]; public let fast: Int; public let slow: Int; public let signal: Int
    public init(macdLine: [IndicatorValue], signalLine: [IndicatorValue], histogram: [IndicatorValue], fast: Int = 12, slow: Int = 26, signal: Int = 9) {
        self.macdLine = macdLine; self.signalLine = signalLine; self.histogram = histogram
        self.fast = fast; self.slow = slow; self.signal = signal
    }
}

public struct RSIRresult: Sendable, Codable {
    public let period: Int; public let values: [IndicatorValue]
    public init(period: Int, values: [IndicatorValue]) { self.period = period; self.values = values }
}

public struct BollingerBands: Sendable, Codable {
    public let period: Int; public let multiplier: Double
    public let upper: [IndicatorValue]; public let middle: [IndicatorValue]; public let lower: [IndicatorValue]
    public init(period: Int = 20, multiplier: Double = 2, upper: [IndicatorValue], middle: [IndicatorValue], lower: [IndicatorValue]) {
        self.period = period; self.multiplier = multiplier; self.upper = upper; self.middle = middle; self.lower = lower
    }
}

public struct ATRResult: Sendable, Codable {
    public let period: Int; public let values: [IndicatorValue]
    public init(period: Int, values: [IndicatorValue]) { self.period = period; self.values = values }
}

public struct StochasticResult: Sendable, Codable {
    public let kPeriod: Int; public let dPeriod: Int
    public let kLine: [IndicatorValue]; public let dLine: [IndicatorValue]
    public init(kPeriod: Int, dPeriod: Int, kLine: [IndicatorValue], dLine: [IndicatorValue]) {
        self.kPeriod = kPeriod; self.dPeriod = dPeriod; self.kLine = kLine; self.dLine = dLine
    }
}

public struct IchimokuResult: Sendable, Codable {
    public let tenkan: [IndicatorValue]; public let kijun: [IndicatorValue]
    public let senkouA: [IndicatorValue]; public let senkouB: [IndicatorValue]; public let chikou: [IndicatorValue]
    public init(tenkan: [IndicatorValue], kijun: [IndicatorValue], senkouA: [IndicatorValue], senkouB: [IndicatorValue], chikou: [IndicatorValue]) {
        self.tenkan = tenkan; self.kijun = kijun; self.senkouA = senkouA; self.senkouB = senkouB; self.chikou = chikou
    }
}

// MARK: - Pattern

public struct DetectedPattern: Sendable, Codable, Identifiable {
    public let id = UUID()
    public let type: PatternType
    public let confidence: Double
    public let startIndex: Int; public let endIndex: Int

    enum CodingKeys: String, CodingKey { case type, confidence, startIndex, endIndex }

    public init(type: PatternType, confidence: Double, startIndex: Int, endIndex: Int) {
        self.type = type; self.confidence = min(1, max(0, confidence))
        self.startIndex = startIndex; self.endIndex = endIndex
    }
}

public enum PatternType: String, Sendable, Codable, CaseIterable {
    case doubleTop, doubleBottom, headAndShoulders, inverseHeadAndShoulders
    case ascendingTriangle, descendingTriangle, symmetricalTriangle
    case cupAndHandle, flag, pennant, wedge, channel
    case support, resistance, breakout, breakdown, gapUp, gapDown
}
