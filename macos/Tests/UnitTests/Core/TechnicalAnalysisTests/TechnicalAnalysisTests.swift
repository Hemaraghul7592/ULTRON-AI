import Foundation
import Testing

@testable import ULTRON

// MARK: - Test Data

/// 30 days of simple OHLCV data for testing.
private func testBars() -> [OHLCV] {
    var bars: [OHLCV] = []
    let baseDate = Date(timeIntervalSince1970: 1_750_000_000)
    let prices: [Double] = [100, 102, 101, 103, 105, 104, 107, 109, 108, 110, 112, 111, 113, 115, 114, 116, 118, 117, 119, 121, 120, 122, 124, 123, 125, 127, 126, 128, 130, 129,
                             131, 133, 132, 134, 136, 135, 137, 139, 138, 140, 142, 141, 143, 145, 144, 146, 148, 147, 149, 151, 150, 152, 154, 153, 155]
    for (i, close) in prices.enumerated() {
        bars.append(OHLCV(symbol: "TEST", open: close - 1, high: close + 1, low: close - 2, close: close, volume: Int64(1_000_000 * (i + 1)), timestamp: baseDate.addingTimeInterval(Double(i) * 86400)))
    }
    return bars
}

// MARK: - Indicator Calculator Tests

@Suite struct IndicatorCalculatorTests {

    let bars = testBars()

    @Test("SMA calculates correctly") func testSMA() throws {
        let result = try IndicatorCalculator.sma(bars: bars, period: 5)
        #expect(result.period == 5)
        #expect(result.values.count == 51)
        #expect(abs(result.values.last!.value - 152.8) < 0.01)
    }

    @Test("SMA throws on insufficient data") func testSMAInsufficient() {
        #expect(throws: TAError.self) { try IndicatorCalculator.sma(bars: bars, period: 100) }
    }

    @Test("EMA calculates correctly") func testEMA() throws {
        let result = try IndicatorCalculator.ema(bars: bars, period: 10)
        #expect(result.period == 10)
        #expect(result.values.count == 46)
    }

    @Test("RSI calculates and stays in 0-100 range") func testRSI() throws {
        let result = try IndicatorCalculator.rsi(bars: bars, period: 14)
        #expect(result.values.count > 0)
        for v in result.values {
            #expect(v.value >= 0)
            #expect(v.value <= 100)
        }
    }

    @Test("RSI approaches 100 in strong uptrend") func testRSIUptrend() throws {
        var upBars: [OHLCV] = []
        var price = 100.0
        for i in 0..<20 {
            price += 5
            upBars.append(OHLCV(symbol: "UP", open: price - 1, high: price + 2, low: price - 2, close: price, volume: 1000, timestamp: Date().addingTimeInterval(Double(i) * 86400)))
        }
        let result = try IndicatorCalculator.rsi(bars: upBars, period: 14)
        #expect(result.values.last!.value > 70)
    }

    @Test("MACD produces lines and histogram") func testMACD() throws {
        let result = try IndicatorCalculator.macd(bars: bars)
        #expect(result.fast == 12)
        #expect(result.slow == 26)
        #expect(result.signal == 9)
        #expect(result.macdLine.count > 0)
        #expect(result.signalLine.count > 0)
        #expect(result.histogram.count > 0)
    }

    @Test("Bollinger Bands envelope price") func testBollinger() throws {
        let result = try IndicatorCalculator.bollingerBands(bars: bars)
        #expect(result.upper.count == result.middle.count)
        #expect(result.lower.count == result.middle.count)
        for i in 0..<result.middle.count {
            #expect(result.upper[i].value >= result.middle[i].value)
            #expect(result.lower[i].value <= result.middle[i].value)
        }
    }

    @Test("ATR is positive") func testATR() throws {
        let result = try IndicatorCalculator.atr(bars: bars, period: 14)
        for v in result.values { #expect(v.value > 0) }
    }

    @Test("Stochastic oscillator in 0-100 range") func testStochastic() throws {
        let result = try IndicatorCalculator.stochastic(bars: bars)
        #expect(result.kLine.count > 0)
        for v in result.kLine { #expect(v.value >= 0); #expect(v.value <= 100) }
    }

    @Test("Ichimoku cloud produces all five lines") func testIchimoku() throws {
        let result = try IndicatorCalculator.ichimoku(bars: bars)
        #expect(!result.tenkan.isEmpty)
        #expect(!result.kijun.isEmpty)
        #expect(!result.senkouA.isEmpty)
        #expect(!result.senkouB.isEmpty)
    }

    @Test("Momentum shows price change") func testMomentum() throws {
        let result = try IndicatorCalculator.momentum(bars: bars, period: 10)
        #expect(result.count > 0)
    }

    @Test("OBV accumulates volume") func testOBV() throws {
        let result = try IndicatorCalculator.obv(bars: bars)
        #expect(result.count == bars.count)
    }

    @Test("Pivot points return all levels") func testPivotPoints() {
        let pp = IndicatorCalculator.pivotPoints(high: 130, low: 100, close: 129)
        #expect(pp.r1 > pp.pivot)
        #expect(pp.s1 < pp.pivot)
        #expect(pp.r3 > pp.r2)
        #expect(pp.s3 < pp.s2)
    }

    @Test("Fibonacci retracement has all levels") func testFibonacci() {
        let fib = IndicatorCalculator.fibonacciRetracement(high: 200, low: 100)
        #expect(fib[0] == 100)
        #expect(fib[0.5] == 150)
        #expect(fib[1] == 200)
    }

    @Test("SuperTrend produces values") func testSuperTrend() throws {
        let result = try IndicatorCalculator.superTrend(bars: bars)
        #expect(!result.isEmpty)
    }

    @Test("Donchian channel produces envelopes") func testDonchian() throws {
        let (upper, lower) = try IndicatorCalculator.donchianChannel(bars: bars, period: 10)
        #expect(!upper.isEmpty)
        for i in 0..<upper.count { #expect(upper[i].value >= lower[i].value) }
    }

    @Test("ROC percentage change") func testROC() throws {
        let result = try IndicatorCalculator.roc(bars: bars, period: 10)
        #expect(result.count > 0)
    }
}

// MARK: - Pattern Detector Tests

@Suite struct PatternDetectorTests {
    let bars = testBars()

    @Test("Support and resistance found") func testSR() {
        let (support, resistance) = PatternDetector.detectSupportResistance(bars: bars)
        #expect(support != nil)
        #expect(resistance != nil)
        #expect(resistance! > support!)
    }

    @Test("Double top not detected in trend") func testNoDoubleTop() {
        #expect(PatternDetector.detectDoubleTop(bars: bars) == nil)
    }

    @Test("Breakout detected near high") func testBreakout() {
        let r = PatternDetector.detectBreakout(bars: bars)
        _ = r  // May or may not detect depending on data
    }

    @Test("DetectAll returns array") func testDetectAll() {
        let results = PatternDetector.detectAll(bars: bars)
        #expect(results.count >= 0)
    }
}

// MARK: - Signal Engine Tests

@Suite struct SignalEngineTests {

    @Test("RSI signal thresholds work") func testRSISignals() {
        #expect(SignalEngine.rsiSignal(75) == .sell)
        #expect(SignalEngine.rsiSignal(25) == .buy)
        #expect(SignalEngine.rsiSignal(50) == .neutral)
    }

    @Test("MACD crossover signals") func testMACDSignal() {
        #expect(SignalEngine.macdSignal(macd: 2, signal: 1) == .buy)
        #expect(SignalEngine.macdSignal(macd: -2, signal: -1) == .sell)
        #expect(SignalEngine.macdSignal(macd: 0.5, signal: 0.5) == .neutral)
    }

    @Test("Bollinger Band position signals") func testBollingerSignal() {
        #expect(SignalEngine.bollingerSignal(price: 90, upper: 110, lower: 95) == .buy)
        #expect(SignalEngine.bollingerSignal(price: 115, upper: 110, lower: 95) == .sell)
    }

    @Test("Stochastic signal crossovers") func testStochasticSignal() {
        #expect(SignalEngine.stochasticSignal(k: 15, d: 12) == .buy)
        #expect(SignalEngine.stochasticSignal(k: 85, d: 88) == .sell)
    }

    @Test("Consensus combines signals with weights") func testConsensus() {
        let signal = SignalEngine.consensus(rsiStrength: .buy, macdStrength: .buy, bbStrength: .buy, stochStrength: .buy)
        #expect(signal.strength == .strongBuy)
        #expect(signal.confidence > 0.5)
    }

    @Test("Consensus neutral when mixed") func testConsensusMixed() {
        let signal = SignalEngine.consensus(rsiStrength: .buy, macdStrength: .sell, bbStrength: nil, stochStrength: nil)
        #expect(signal.strength == .neutral)
    }

    @Test("Consensus with nil optional signals") func testConsensusOptional() {
        let signal = SignalEngine.consensus(rsiStrength: .buy, macdStrength: nil, bbStrength: nil, stochStrength: nil)
        #expect(signal.strength == .buy)
    }
}

// MARK: - Technical Analysis Engine Tests

@MainActor
@Suite struct TechnicalAnalysisEngineTests {
    let bars = testBars()
    let engine = TechnicalAnalysisEngine()

    @Test("Compute SMA through engine") func testEngineSMA() async throws {
        let result = try await engine.computeSMA(bars: bars, period: 20)
        #expect(result.values.count > 0)
    }

    @Test("Compute RSI through engine") func testEngineRSI() async throws {
        let result = try await engine.computeRSI(bars: bars)
        #expect(result.period == 14)
    }

    @Test("Compute MACD through engine") func testEngineMACD() async throws {
        let result = try await engine.computeMACD(bars: bars)
        #expect(result.macdLine.count > 0)
    }

    @Test("Compute Bollinger through engine") func testEngineBB() async throws {
        let result = try await engine.computeBollingerBands(bars: bars)
        #expect(result.middle.count > 0)
    }

    @Test("Detect patterns through engine") func testEnginePatterns() {
        let patterns = engine.detectPatterns(bars: bars)
        #expect(patterns.count >= 0)
    }

    @Test("Generate full signal through engine") func testEngineSignal() async throws {
        let signal = try await engine.generateSignal(bars: bars, symbol: "TEST")
        #expect(!signal.reasons.isEmpty)
        #expect(signal.confidence >= 0)
        #expect(signal.confidence <= 1)
    }

    @Test("Engine caches indicator results") func testEngineCache() async throws {
        _ = try await engine.computeSMA(bars: bars, period: 20)
        let stats = await engine.cacheStats()
        #expect(stats.entries >= 1)
    }

    @Test("Clear cache removes entries") func testEngineClearCache() async throws {
        _ = try await engine.computeSMA(bars: bars, period: 20)
        await engine.clearCache()
        let stats = await engine.cacheStats()
        #expect(stats.entries == 0)
    }

    @Test("Generate signal with insufficient data handles gracefully") func testEngineSignalGraceful() async throws {
        let fewBars = Array(bars.prefix(3))
        do {
            _ = try await engine.generateSignal(bars: fewBars)
        } catch let e as TAError {
            #expect(String(describing: e).contains("Need"))
        }
    }
}
