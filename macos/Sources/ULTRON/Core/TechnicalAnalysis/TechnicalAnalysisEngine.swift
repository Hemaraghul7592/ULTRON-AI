import Foundation

/// The central entry point for all technical analysis operations in ULTRON.
///
/// Provides typed methods for computing indicators, detecting patterns,
/// and generating signals. All market data comes from `FinancialEngine`.
///
/// This engine is stateless — every method takes input data and returns
/// a computed result. Caching is handled internally via `IndicatorCache`.
@MainActor
public final class TechnicalAnalysisEngine {

    public let config: TAConfig
    private let cache = IndicatorCache()

    public init(config: TAConfig = .default) {
        self.config = config
    }

    // MARK: - Indicators

    public func computeSMA(bars: [OHLCV], period: Int? = nil, symbol: String = "") async throws -> SMA {
        let p = period ?? config.defaultSMAPeriods[0]
        if config.cacheEnabled, let cached: SMA = await cache.get(cacheKey("sma", symbol, p)) { return cached }
        let result = try IndicatorCalculator.sma(bars: bars, period: p)
        if config.cacheEnabled { await cache.set(cacheKey("sma", symbol, p), value: result) }
        return result
    }

    public func computeEMA(bars: [OHLCV], period: Int? = nil, symbol: String = "") async throws -> EMA {
        let p = period ?? config.defaultEMAPeriods[0]
        if config.cacheEnabled, let cached: EMA = await cache.get(cacheKey("ema", symbol, p)) { return cached }
        let result = try IndicatorCalculator.ema(bars: bars, period: p)
        if config.cacheEnabled { await cache.set(cacheKey("ema", symbol, p), value: result) }
        return result
    }

    public func computeMACD(bars: [OHLCV], symbol: String = "") async throws -> MACDResult {
        if config.cacheEnabled, let cached: MACDResult = await cache.get(cacheKey("macd", symbol)) { return cached }
        let result = try IndicatorCalculator.macd(bars: bars, fast: config.defaultMACDFast, slow: config.defaultMACDSlow, signal: config.defaultMACDSignal)
        if config.cacheEnabled { await cache.set(cacheKey("macd", symbol), value: result) }
        return result
    }

    public func computeRSI(bars: [OHLCV], period: Int? = nil, symbol: String = "") async throws -> RSIRresult {
        let p = period ?? config.defaultRSIPeriod
        if config.cacheEnabled, let cached: RSIRresult = await cache.get(cacheKey("rsi", symbol, p)) { return cached }
        let result = try IndicatorCalculator.rsi(bars: bars, period: p)
        if config.cacheEnabled { await cache.set(cacheKey("rsi", symbol, p), value: result) }
        return result
    }

    public func computeBollingerBands(bars: [OHLCV], symbol: String = "") async throws -> BollingerBands {
        if config.cacheEnabled, let cached: BollingerBands = await cache.get(cacheKey("bb", symbol)) { return cached }
        let result = try IndicatorCalculator.bollingerBands(bars: bars, period: config.defaultBBPeriod, multiplier: config.defaultBBMultiplier)
        if config.cacheEnabled { await cache.set(cacheKey("bb", symbol), value: result) }
        return result
    }

    public func computeATR(bars: [OHLCV], period: Int? = nil, symbol: String = "") async throws -> ATRResult {
        let p = period ?? config.defaultATRPeriod
        if config.cacheEnabled, let cached: ATRResult = await cache.get(cacheKey("atr", symbol, p)) { return cached }
        let result = try IndicatorCalculator.atr(bars: bars, period: p)
        if config.cacheEnabled { await cache.set(cacheKey("atr", symbol, p), value: result) }
        return result
    }

    public func computeStochastic(bars: [OHLCV], symbol: String = "") async throws -> StochasticResult {
        if config.cacheEnabled, let cached: StochasticResult = await cache.get(cacheKey("stoch", symbol)) { return cached }
        let result = try IndicatorCalculator.stochastic(bars: bars, kPeriod: config.defaultStochasticK, dPeriod: config.defaultStochasticD)
        if config.cacheEnabled { await cache.set(cacheKey("stoch", symbol), value: result) }
        return result
    }

    // MARK: - Patterns

    public func detectPatterns(bars: [OHLCV]) -> [DetectedPattern] {
        PatternDetector.detectAll(bars: bars)
    }

    // MARK: - Signals

    /// Generates a full consensus signal from all indicators.
    public func generateSignal(bars: [OHLCV], symbol: String = "") async throws -> TASignal {
        let rsi = try await computeRSI(bars: bars, symbol: symbol)
        let rsiLast = rsi.values.last?.value ?? 50
        let rsiStrength = SignalEngine.rsiSignal(rsiLast)

        let macd: MACDResult
        var macdStrength: TASignal.Strength?
        do { macd = try await computeMACD(bars: bars, symbol: symbol)
            if let ml = macd.macdLine.last, let sl = macd.signalLine.last {
                macdStrength = SignalEngine.macdSignal(macd: ml.value, signal: sl.value)
            }
        } catch { macdStrength = nil }

        let bb: BollingerBands
        var bbStrength: TASignal.Strength?
        do { bb = try await computeBollingerBands(bars: bars, symbol: symbol)
            if let price = bars.last?.close, let u = bb.upper.last, let l = bb.lower.last {
                bbStrength = SignalEngine.bollingerSignal(price: price, upper: u.value, lower: l.value)
            }
        } catch { bbStrength = nil }

        let stoch: StochasticResult
        var stochStrength: TASignal.Strength?
        do { stoch = try await computeStochastic(bars: bars, symbol: symbol)
            if let k = stoch.kLine.last, let d = stoch.dLine.last {
                stochStrength = SignalEngine.stochasticSignal(k: k.value, d: d.value)
            }
        } catch { stochStrength = nil }

        return SignalEngine.consensus(rsiStrength: rsiStrength, macdStrength: macdStrength, bbStrength: bbStrength, stochStrength: stochStrength)
    }

    /// Clears the indicator cache.
    public func clearCache() async { await cache.clear() }

    /// Returns cache statistics.
    public func cacheStats() async -> (entries: Int, hits: Int, misses: Int) {
        (await cache.count, await cache.hits, await cache.misses)
    }

    private func cacheKey(_ indicator: String, _ symbol: String, _ param: Int = 0) -> String {
        "\(indicator):\(symbol):\(param)"
    }
}
