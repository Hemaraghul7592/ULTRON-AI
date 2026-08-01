import Foundation

/// Detects chart patterns in OHLCV data.
///
/// Patterns are identified using local extrema detection, trend line analysis,
/// and geometric pattern matching against the price series.
public enum PatternDetector {

    /// Detects support and resistance levels using swing points.
    public static func detectSupportResistance(bars: [OHLCV], lookback: Int = 20) -> (support: Double?, resistance: Double?) {
        guard bars.count >= lookback else { return (nil, nil) }
        let slice = bars.suffix(lookback)
        let highs = slice.map(\.high).sorted()
        let lows = slice.map(\.low).sorted()
        let resistance = highs.suffix(2).reduce(0, +) / 2
        let support = lows.prefix(2).reduce(0, +) / 2
        return (support, resistance)
    }

    /// Detects double top pattern using swing high comparison.
    public static func detectDoubleTop(bars: [OHLCV], tolerance: Double = 0.03) -> DetectedPattern? {
        guard bars.count >= 20 else { return nil }
        let swings = findSwingHighs(bars: bars, lookback: 5)
        guard swings.count >= 2 else { return nil }
        let last = swings.suffix(2)
        let h1 = last.first!, h2 = last.last!
        let diff = abs(h1.value - h2.value) / h1.value
        if diff <= tolerance && h2.timestamp > h1.timestamp {
            return DetectedPattern(type: .doubleTop, confidence: 1 - diff, startIndex: h1.index, endIndex: h2.index)
        }
        return nil
    }

    /// Detects double bottom pattern using swing low comparison.
    public static func detectDoubleBottom(bars: [OHLCV], tolerance: Double = 0.03) -> DetectedPattern? {
        guard bars.count >= 20 else { return nil }
        let swings = findSwingLows(bars: bars, lookback: 5)
        guard swings.count >= 2 else { return nil }
        let last = swings.suffix(2)
        let l1 = last.first!, l2 = last.last!
        let diff = abs(l1.value - l2.value) / l1.value
        if diff <= tolerance && l2.timestamp > l1.timestamp {
            return DetectedPattern(type: .doubleBottom, confidence: 1 - diff, startIndex: l1.index, endIndex: l2.index)
        }
        return nil
    }

    /// Detects breakout above resistance.
    public static func detectBreakout(bars: [OHLCV]) -> DetectedPattern? {
        let (_, resistance) = detectSupportResistance(bars: bars)
        guard let r = resistance, let last = bars.last else { return nil }
        if last.close > r * 1.01 {
            return DetectedPattern(type: .breakout, confidence: min(1, (last.close - r) / r * 100), startIndex: bars.count - 1, endIndex: bars.count - 1)
        }
        return nil
    }

    /// Detects all patterns in a dataset.
    public static func detectAll(bars: [OHLCV]) -> [DetectedPattern] {
        var results: [DetectedPattern] = []
        if let p = detectDoubleTop(bars: bars) { results.append(p) }
        if let p = detectDoubleBottom(bars: bars) { results.append(p) }
        if let p = detectBreakout(bars: bars) { results.append(p) }
        return results
    }

    // MARK: - Helpers

    private struct SwingPoint { let index: Int; let value: Double; let timestamp: Date }

    private static func findSwingHighs(bars: [OHLCV], lookback: Int) -> [SwingPoint] {
        var swings: [SwingPoint] = []
        for i in lookback..<(bars.count - lookback) {
            let before = bars[(i - lookback)..<i].map(\.high)
            let after = bars[(i + 1)...(i + lookback)].map(\.high)
            if bars[i].high >= before.max()! && bars[i].high > after.max()! {
                swings.append(SwingPoint(index: i, value: bars[i].high, timestamp: bars[i].timestamp))
            }
        }
        return swings
    }

    private static func findSwingLows(bars: [OHLCV], lookback: Int) -> [SwingPoint] {
        var swings: [SwingPoint] = []
        for i in lookback..<(bars.count - lookback) {
            let before = bars[(i - lookback)..<i].map(\.low)
            let after = bars[(i + 1)...(i + lookback)].map(\.low)
            if bars[i].low <= before.min()! && bars[i].low < after.min()! {
                swings.append(SwingPoint(index: i, value: bars[i].low, timestamp: bars[i].timestamp))
            }
        }
        return swings
    }
}
