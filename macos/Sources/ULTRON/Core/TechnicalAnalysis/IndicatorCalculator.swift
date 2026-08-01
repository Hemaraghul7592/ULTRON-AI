import Foundation

/// Stateless technical indicator calculations.
///
/// Every method takes raw OHLCV data and returns a typed result.
/// All calculations are deterministic and independent — no shared state.
public enum IndicatorCalculator {

    // MARK: - Validation

    private static func validate(_ bars: [OHLCV], min: Int) throws {
        guard bars.count >= max(1, min) else {
            throw TAError.insufficientData(required: min, available: bars.count)
        }
    }

    // MARK: - SMA

    public static func sma(bars: [OHLCV], period: Int) throws -> SMA {
        try validate(bars, min: period)
        var values: [IndicatorValue] = []
        for i in (period - 1)..<bars.count {
            let sum = bars[(i - period + 1)...i].reduce(0) { $0 + $1.close }
            values.append(IndicatorValue(timestamp: bars[i].timestamp, value: sum / Double(period)))
        }
        return SMA(period: period, values: values)
    }

    // MARK: - EMA

    public static func ema(bars: [OHLCV], period: Int) throws -> EMA {
        try validate(bars, min: period)
        let multiplier = 2.0 / (Double(period) + 1.0)
        var values: [IndicatorValue] = []
        let firstSMA = bars[0..<period].reduce(0) { $0 + $1.close } / Double(period)
        var prev = firstSMA
        values.append(IndicatorValue(timestamp: bars[period - 1].timestamp, value: prev))
        for i in period..<bars.count {
            prev = (bars[i].close - prev) * multiplier + prev
            values.append(IndicatorValue(timestamp: bars[i].timestamp, value: prev))
        }
        return EMA(period: period, values: values)
    }

    // MARK: - MACD

    public static func macd(bars: [OHLCV], fast: Int = 12, slow: Int = 26, signal: Int = 9) throws -> MACDResult {
        try validate(bars, min: slow + signal)
        let fastEMA = try ema(bars: bars, period: fast)
        let slowEMA = try ema(bars: bars, period: slow)
        let offset = fastEMA.values.count - slowEMA.values.count
        var macdValues: [IndicatorValue] = []
        for i in 0..<slowEMA.values.count {
            let diff = fastEMA.values[i + offset].value - slowEMA.values[i].value
            macdValues.append(IndicatorValue(timestamp: slowEMA.values[i].timestamp, value: diff))
        }
        let signalLine = smaRaw(values: macdValues, period: signal)
        var histValues: [IndicatorValue] = []
        for i in signal..<macdValues.count {
            histValues.append(IndicatorValue(timestamp: macdValues[i].timestamp, value: macdValues[i].value - signalLine[i - signal].value))
        }
        return MACDResult(macdLine: macdValues, signalLine: signalLine, histogram: histValues)
    }

    // MARK: - RSI

    public static func rsi(bars: [OHLCV], period: Int = 14) throws -> RSIRresult {
        try validate(bars, min: period + 1)
        var gains = 0.0; var losses = 0.0
        var values: [IndicatorValue] = []
        for i in 1..<period + 1 { let d = bars[i].close - bars[i - 1].close; if d > 0 { gains += d } else { losses -= d } }
        var avgGain = gains / Double(period); var avgLoss = losses / Double(period)
        let rs = avgLoss == 0 ? 100 : avgGain / avgLoss
        values.append(IndicatorValue(timestamp: bars[period].timestamp, value: 100 - 100 / (1 + rs)))
        for i in (period + 1)..<bars.count {
            let d = bars[i].close - bars[i - 1].close; let g = d > 0 ? d : 0; let l = d < 0 ? -d : 0
            avgGain = (avgGain * Double(period - 1) + g) / Double(period)
            avgLoss = (avgLoss * Double(period - 1) + l) / Double(period)
            let r = avgLoss == 0 ? 100 : avgGain / avgLoss
            values.append(IndicatorValue(timestamp: bars[i].timestamp, value: 100 - 100 / (1 + r)))
        }
        return RSIRresult(period: period, values: values)
    }

    // MARK: - Bollinger Bands

    public static func bollingerBands(bars: [OHLCV], period: Int = 20, multiplier: Double = 2) throws -> BollingerBands {
        try validate(bars, min: period)
        let smaResult = try sma(bars: bars, period: period)
        var upper = [IndicatorValue](), middle = smaResult.values, lower = [IndicatorValue]()
        for i in (period - 1)..<bars.count {
            let slice = bars[(i - period + 1)...i]
            let mean = smaResult.values[i - period + 1].value
            let variance = slice.reduce(0) { $0 + pow($1.close - mean, 2) } / Double(period)
            let stdDev = sqrt(variance)
            upper.append(IndicatorValue(timestamp: bars[i].timestamp, value: mean + multiplier * stdDev))
            lower.append(IndicatorValue(timestamp: bars[i].timestamp, value: mean - multiplier * stdDev))
        }
        return BollingerBands(period: period, multiplier: multiplier, upper: upper, middle: middle, lower: lower)
    }

    // MARK: - ATR

    public static func atr(bars: [OHLCV], period: Int = 14) throws -> ATRResult {
        try validate(bars, min: period + 1)
        var trValues: [Double] = []
        for i in 1..<bars.count {
            let h_l = bars[i].high - bars[i].low
            let h_pc = abs(bars[i].high - bars[i - 1].close)
            let l_pc = abs(bars[i].low - bars[i - 1].close)
            trValues.append(max(h_l, h_pc, l_pc))
        }
        var values: [IndicatorValue] = []
        let firstATR = trValues[0..<period].reduce(0, +) / Double(period)
        values.append(IndicatorValue(timestamp: bars[period].timestamp, value: firstATR))
        var prevATR = firstATR
        for i in period..<trValues.count {
            prevATR = (prevATR * Double(period - 1) + trValues[i]) / Double(period)
            values.append(IndicatorValue(timestamp: bars[i + 1].timestamp, value: prevATR))
        }
        return ATRResult(period: period, values: values)
    }

    // MARK: - Stochastic Oscillator

    public static func stochastic(bars: [OHLCV], kPeriod: Int = 14, dPeriod: Int = 3) throws -> StochasticResult {
        try validate(bars, min: kPeriod)
        var kValues: [IndicatorValue] = []
        for i in (kPeriod - 1)..<bars.count {
            let slice = bars[(i - kPeriod + 1)...i]
            let hh = slice.map(\.high).max()!
            let ll = slice.map(\.low).min()!
            let pctK = (hh - ll) == 0 ? 50 : (bars[i].close - ll) / (hh - ll) * 100
            kValues.append(IndicatorValue(timestamp: bars[i].timestamp, value: pctK))
        }
        let dValues = smaRaw(values: kValues, period: dPeriod)
        return StochasticResult(kPeriod: kPeriod, dPeriod: dPeriod, kLine: kValues, dLine: dValues)
    }

    // MARK: - Ichimoku Cloud

    public static func ichimoku(bars: [OHLCV]) throws -> IchimokuResult {
        try validate(bars, min: 52)
        func midpoint(_ slice: ArraySlice<OHLCV>) -> Double { (slice.map(\.high).max()! + slice.map(\.low).min()!) / 2 }
        var tenkan = [IndicatorValue](), kijun = [IndicatorValue](), senkouA = [IndicatorValue](), senkouB = [IndicatorValue](), chikou = [IndicatorValue]()
        for i in 25..<bars.count {
            tenkan.append(IndicatorValue(timestamp: bars[i].timestamp, value: midpoint(bars[(i - 8)...i])))
            kijun.append(IndicatorValue(timestamp: bars[i].timestamp, value: midpoint(bars[(i - 25)...i])))
        }
        for i in 51..<bars.count {
            let t = tenkan[i - 26].value; let k = kijun[i - 26].value
            senkouA.append(IndicatorValue(timestamp: bars[i].timestamp, value: (t + k) / 2))
            senkouB.append(IndicatorValue(timestamp: bars[i].timestamp, value: midpoint(bars[(i - 51)...i])))
        }
        for i in 26..<bars.count {
            chikou.append(IndicatorValue(timestamp: bars[i - 26].timestamp, value: bars[i].close))
        }
        return IchimokuResult(tenkan: tenkan, kijun: kijun, senkouA: senkouA, senkouB: senkouB, chikou: chikou)
    }

    // MARK: - Momentum / ROC

    public static func momentum(bars: [OHLCV], period: Int = 10) throws -> [IndicatorValue] {
        try validate(bars, min: period)
        return (period..<bars.count).map { i in
            IndicatorValue(timestamp: bars[i].timestamp, value: bars[i].close - bars[i - period].close)
        }
    }

    public static func roc(bars: [OHLCV], period: Int = 10) throws -> [IndicatorValue] {
        try validate(bars, min: period)
        return (period..<bars.count).map { i in
            IndicatorValue(timestamp: bars[i].timestamp, value: (bars[i].close - bars[i - period].close) / bars[i - period].close * 100)
        }
    }

    // MARK: - OBV

    public static func obv(bars: [OHLCV]) throws -> [IndicatorValue] {
        try validate(bars, min: 1)
        var obv = 0.0
        var values = [IndicatorValue(timestamp: bars[0].timestamp, value: 0)]
        for i in 1..<bars.count {
            if bars[i].close > bars[i - 1].close { obv += Double(bars[i].volume) }
            else if bars[i].close < bars[i - 1].close { obv -= Double(bars[i].volume) }
            values.append(IndicatorValue(timestamp: bars[i].timestamp, value: obv))
        }
        return values
    }

    // MARK: - Pivot Points (Classic)

    public static func pivotPoints(high: Double, low: Double, close: Double) -> (pivot: Double, r1: Double, r2: Double, r3: Double, s1: Double, s2: Double, s3: Double) {
        let pp = (high + low + close) / 3
        return (pp, 2 * pp - low, pp + (high - low), pp + 2 * (high - low), 2 * pp - high, pp - (high - low), pp - 2 * (high - low))
    }

    // MARK: - Fibonacci Retracement

    public static func fibonacciRetracement(high: Double, low: Double) -> [Double: Double] {
        let diff = high - low
        return [0: low, 0.236: low + 0.236 * diff, 0.382: low + 0.382 * diff, 0.5: low + 0.5 * diff, 0.618: low + 0.618 * diff, 0.786: low + 0.786 * diff, 1: high]
    }

    // MARK: - SuperTrend

    public static func superTrend(bars: [OHLCV], period: Int = 10, multiplier: Double = 3.0) throws -> [IndicatorValue] {
        let atrResult = try atr(bars: bars, period: period)
        var values: [IndicatorValue] = []
        var trend: Double = 1
        let offset = atrResult.values.count - (bars.count - period)
        for i in period..<bars.count {
            let atrIdx = i - period + offset
            guard atrIdx >= 0, atrIdx < atrResult.values.count else { continue }
            let atrVal = atrResult.values[atrIdx].value
            let upper = (bars[i].high + bars[i].low) / 2 + multiplier * atrVal
            let lower = (bars[i].high + bars[i].low) / 2 - multiplier * atrVal
            if bars[i].close > upper { trend = 1 }
            else if bars[i].close < lower { trend = -1 }
            values.append(IndicatorValue(timestamp: bars[i].timestamp, value: trend > 0 ? lower : upper))
        }
        return values
    }

    // MARK: - Donchian Channel

    public static func donchianChannel(bars: [OHLCV], period: Int = 20) throws -> (upper: [IndicatorValue], lower: [IndicatorValue]) {
        try validate(bars, min: period)
        var upper = [IndicatorValue](), lower = [IndicatorValue]()
        for i in (period - 1)..<bars.count {
            let slice = bars[(i - period + 1)...i]
            upper.append(IndicatorValue(timestamp: bars[i].timestamp, value: slice.map(\.high).max()!))
            lower.append(IndicatorValue(timestamp: bars[i].timestamp, value: slice.map(\.low).min()!))
        }
        return (upper, lower)
    }

    // MARK: - Helper: SMA on IndicatorValues

    private static func smaRaw(values: [IndicatorValue], period: Int) -> [IndicatorValue] {
        guard values.count >= period else { return [] }
        var result: [IndicatorValue] = []
        for i in (period - 1)..<values.count {
            let sum = values[(i - period + 1)...i].reduce(0) { $0 + $1.value }
            result.append(IndicatorValue(timestamp: values[i].timestamp, value: sum / Double(period)))
        }
        return result
    }
}
