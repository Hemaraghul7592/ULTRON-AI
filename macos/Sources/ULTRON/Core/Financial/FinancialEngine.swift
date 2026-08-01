import Foundation

/// The central entry point for all financial operations in ULTRON.
///
/// `FinancialEngine` owns the provider registry, cache, and coordination
/// logic. Every future financial feature (portfolio, technical analysis,
/// screening) will route through this engine.
///
/// The engine never calls external APIs directly — it delegates to
/// registered `FinancialProvider` instances. Provider selection is
/// driven by capability matching and configured priorities.
///
/// ## Thread Safety
///
/// Confined to `@MainActor` for integration with DI and lifecycle.
@MainActor
public final class FinancialEngine {

    // MARK: - Properties

    public let config: FinancialConfig
    public let logger: Logger

    private let quoteCache: FinancialCache<String, Quote>
    private let ohlcvCache: FinancialCache<String, [OHLCV]>
    private let companyCache: FinancialCache<String, CompanyProfile>
    private var providers: [any FinancialProvider] = []
    private var registry = FinancialRegistry()

    // MARK: - Initialization

    public init(config: FinancialConfig = .init(), logger: Logger) {
        self.config = config
        self.logger = logger
        quoteCache = FinancialCache(defaultTTL: config.quoteCacheTTL)
        ohlcvCache = FinancialCache(defaultTTL: config.ohlcvCacheTTL)
        companyCache = FinancialCache(defaultTTL: config.companyCacheTTL)
    }

    // MARK: - Provider Management

    /// Registers a financial provider.
    public func registerProvider(_ provider: any FinancialProvider) async {
        providers.removeAll { $0.providerID == provider.providerID }
        providers.append(provider)
        providers.sort { a, b in
            let aIdx = config.quoteProviderPriority.firstIndex(of: a.providerID) ?? Int.max
            let bIdx = config.quoteProviderPriority.firstIndex(of: b.providerID) ?? Int.max
            return aIdx < bIdx
        }
        await logger.info("Financial provider registered", metadata: ["provider": provider.providerID])
    }

    /// Returns registered provider IDs.
    public func registeredProviderIDs() -> [String] {
        providers.map(\.providerID)
    }

    // MARK: - Registry

    /// Updates the capability registry for a provider.
    public func updateRegistry(for provider: any FinancialProvider, capabilities: Set<FinancialCapability>, exchanges: Set<String> = [], symbols: Set<String> = []) {
        registry.register(providerID: provider.providerID, capabilities: capabilities, exchanges: exchanges, symbols: symbols)
    }

    /// Returns provider IDs supporting a capability.
    public func providers(for capability: FinancialCapability) -> [String] {
        registry.providers(for: capability)
    }

    // MARK: - Quotes

    /// Fetches a quote for a symbol, using cache if available.
    public func fetchQuote(symbol: String) async throws -> Quote {
        if let cached = await quoteCache.get(symbol) { return cached }

        guard let provider = selectProvider(for: symbol, capability: .quotes) else {
            throw FinancialError.symbolNotFound(symbol)
        }

        let quote = try await provider.fetchQuote(symbol: symbol)
        await quoteCache.set(symbol, value: quote)
        return quote
    }

    // MARK: - OHLCV

    /// Fetches OHLCV bars for a symbol and range.
    public func fetchOHLCV(symbol: String, range: OHLCVRange = .oneDay) async throws -> [OHLCV] {
        let cacheKey = "\(symbol):\(range.rawValue)"
        if let cached = await ohlcvCache.get(cacheKey) { return cached }

        guard let provider = selectProvider(for: symbol, capability: .ohlcv) else {
            throw FinancialError.symbolNotFound(symbol)
        }

        let bars = try await provider.fetchOHLCV(symbol: symbol, range: range)
        await ohlcvCache.set(cacheKey, value: bars)
        return bars
    }

    // MARK: - Company Profile

    /// Fetches company profile data.
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        if let cached = await companyCache.get(symbol) { return cached }

        guard let provider = selectProvider(for: symbol, capability: .companyProfile) else {
            throw FinancialError.symbolNotFound(symbol)
        }

        let profile = try await provider.fetchCompanyProfile(symbol: symbol)
        await companyCache.set(symbol, value: profile)
        return profile
    }

    // MARK: - Cache

    /// Clears all caches.
    public func clearCache() async {
        await quoteCache.clear()
        await ohlcvCache.clear()
        await companyCache.clear()
    }

    /// Returns cache statistics.
    public func cacheStats() async -> [(name: String, entries: Int, hitRatio: Double)] {
        [
            ("quotes", await quoteCache.count, await quoteCache.hitRatio),
            ("ohlcv", await ohlcvCache.count, await ohlcvCache.hitRatio),
            ("company", await companyCache.count, await companyCache.hitRatio),
        ]
    }

    // MARK: - Health

    /// Returns provider health summary.
    public func health() -> [(providerID: String, registered: Bool)] {
        providers.map { ($0.providerID, true) }
    }

    // MARK: - Helpers

    /// Selects the best available provider for a symbol and capability.
    private func selectProvider(for symbol: String, capability: FinancialCapability) -> (any FinancialProvider)? {
        let orderedIDs = registry.providers(for: capability)
        for id in orderedIDs {
            if let provider = providers.first(where: { $0.providerID == id }) {
                return provider
            }
        }
        return providers.first
    }
}
