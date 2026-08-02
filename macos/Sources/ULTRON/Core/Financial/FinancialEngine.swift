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
    private var providerByID: [String: any FinancialProvider] = [:]
    private var registry = FinancialRegistry()
    private var orderedProviderIDs: [FinancialCapability: [String]] = [:]
    private var priorityByProviderCapability: [String: [FinancialCapability: Int]] = [:]
    private var healthByProvider: [String: HealthStatus] = [:]
    private var breakers: [String: CircuitBreaker] = [:]
    private var metricsByProvider: [String: ProviderMetrics] = [:]

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
        providerByID[provider.providerID] = provider
        providers.append(provider)
        breakers[provider.providerID] = CircuitBreaker()
        metricsByProvider[provider.providerID] = ProviderMetrics()
        healthByProvider.removeValue(forKey: provider.providerID)
        priorityByProviderCapability.removeValue(forKey: provider.providerID)
        orderedProviderIDs.removeAll()
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
    public func updateRegistry(for provider: any FinancialProvider, capabilities: Set<FinancialCapability>, exchanges: Set<String> = [], symbols: Set<String> = [], priority: Int? = nil, enabled: Bool = true) {
        let priorities = Dictionary(uniqueKeysWithValues: capabilities.map { capability in
            (capability, priority ?? capabilityPriority(for: provider.providerID, capabilities: [capability]))
        })
        priorityByProviderCapability[provider.providerID] = priorities
        registry.register(providerID: provider.providerID, capabilities: capabilities, exchanges: exchanges, symbols: symbols, priority: priority ?? priorities.values.min() ?? Int.max, enabled: enabled)
        orderedProviderIDs.removeAll()
    }

    /// Returns provider IDs supporting a capability.
    public func providers(for capability: FinancialCapability) -> [String] {
        registry.providers(for: capability)
    }

    // MARK: - Quotes

    /// Fetches a quote for a symbol, using cache if available.
    public func fetchQuote(symbol: String) async throws -> Quote {
        if let cached = await quoteCache.get(symbol) { return cached }

        let quote = try await executeWithFailover(capability: .quotes) { provider in
            try await provider.fetchQuote(symbol: symbol)
        }
        await quoteCache.set(symbol, value: quote)
        return quote
    }

    // MARK: - OHLCV

    /// Fetches OHLCV bars for a symbol and range.
    public func fetchOHLCV(symbol: String, range: OHLCVRange = .oneDay) async throws -> [OHLCV] {
        let cacheKey = "\(symbol):\(range.rawValue)"
        if let cached = await ohlcvCache.get(cacheKey) { return cached }

        let bars = try await executeWithFailover(capability: .ohlcv) { provider in
            try await provider.fetchOHLCV(symbol: symbol, range: range)
        }
        await ohlcvCache.set(cacheKey, value: bars)
        return bars
    }

    // MARK: - Company Profile

    /// Fetches company profile data.
    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        if let cached = await companyCache.get(symbol) { return cached }

        let profile = try await executeWithFailover(capability: .companyProfile) { provider in
            try await provider.fetchCompanyProfile(symbol: symbol)
        }
        await companyCache.set(symbol, value: profile)
        return profile
    }

    /// Fetches current market indices from the registered provider.
    public func fetchIndices() async throws -> [MarketIndex] {
        return try await executeWithFailover(capability: .marketIndices) { provider in
            try await provider.fetchIndices()
        }
    }

    /// Fetches financial news from the registered provider.
    public func fetchNews(symbols: [String] = []) async throws -> [NewsArticle] {
        return try await executeWithFailover(capability: .news) { provider in
            try await provider.fetchNews(symbols: symbols)
        }
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

    /// Returns routing and request metrics for a registered provider.
    public func metrics(for providerID: String) -> ProviderMetrics? {
        metricsByProvider[providerID]
    }

    // MARK: - Helpers

    /// Returns the ordered, healthy, circuit-available providers for a capability.
    private func selectProviders(for capability: FinancialCapability) async throws -> [any FinancialProvider] {
        var candidates: [any FinancialProvider] = []

        let orderedIDs = orderedProviderIDs[capability] ?? orderedIDs(for: capability)
        orderedProviderIDs[capability] = orderedIDs
        for providerID in orderedIDs {
            guard let provider = providerByID[providerID] else { continue }
            guard registry.isEnabled(providerID: providerID) else {
                record(for: providerID) { $0.recordSkipped() }
                continue
            }
            guard provider.financialCapabilities.contains(capability) else {
                record(for: providerID) { $0.recordCapabilityMismatch(); $0.recordSkipped() }
                continue
            }

            let health = await health(for: provider)
            guard health == .healthy else {
                record(for: providerID) { $0.recordHealthFailure(); $0.recordSkipped() }
                continue
            }
            guard let breaker = breakers[providerID], await breaker.allowRequest() else {
                record(for: providerID) { $0.recordCircuitOpen(); $0.recordSkipped() }
                continue
            }
            candidates.append(provider)
        }

        guard !candidates.isEmpty else {
            throw FinancialError.providerNotAvailable(capability.rawValue)
        }
        return candidates
    }

    private func executeWithFailover<T: Sendable>(
        capability: FinancialCapability,
        operation: (any FinancialProvider) async throws -> T
    ) async throws -> T {
        let candidates = try await selectProviders(for: capability)
        var failures: [String] = []

        for (index, provider) in candidates.enumerated() {
            let providerID = provider.providerID
            record(for: providerID) { $0.recordSelected() }
            do {
                let result = try await operation(provider)
                await breakers[providerID]?.recordSuccess()
                healthByProvider[providerID] = .healthy
                if index > 0 { record(for: providerID) { $0.recordSuccessfulFailover() } }
                return result
            } catch {
                let message = String(describing: error)
                failures.append("\(providerID): \(message)")
                record(for: providerID) { $0.recordFailure(error: message) }
                await breakers[providerID]?.recordFailure()
                if !isRetryable(error) {
                    record(for: providerID) { $0.recordFinalFailure() }
                    throw error
                }
            }
        }

        if let lastProviderID = candidates.last?.providerID {
            record(for: lastProviderID) { $0.recordFinalFailure() }
        }
        throw FinancialError.providerFailures(capability: capability.rawValue, failures: failures)
    }

    private func health(for provider: any FinancialProvider) async -> HealthStatus {
        if let cached = healthByProvider[provider.providerID] { return cached }
        let status = await provider.healthCheck()
        healthByProvider[provider.providerID] = status
        return status
    }

    private func record(for providerID: String, update: (inout ProviderMetrics) -> Void) {
        guard var metrics = metricsByProvider[providerID] else { return }
        update(&metrics)
        metricsByProvider[providerID] = metrics
    }

    private func capabilityPriority(for providerID: String, capabilities: Set<FinancialCapability>) -> Int {
        capabilities.compactMap { capability in
            switch capability {
            case .quotes: config.quoteProviderPriority.firstIndex(of: providerID)
            case .ohlcv: config.ohlcvProviderPriority.firstIndex(of: providerID)
            case .companyProfile: config.companyProviderPriority.firstIndex(of: providerID)
            default: nil
            }
        }.min() ?? Int.max
    }

    private func orderedIDs(for capability: FinancialCapability) -> [String] {
        let registryIDs = registry.providers(for: capability)
        return registryIDs.enumerated().sorted { lhs, rhs in
            let leftPriority = priorityByProviderCapability[lhs.element]?[capability] ?? Int.max
            let rightPriority = priorityByProviderCapability[rhs.element]?[capability] ?? Int.max
            if leftPriority != rightPriority { return leftPriority < rightPriority }
            return lhs.offset < rhs.offset
        }.map(\.element)
    }

    private func isRetryable(_ error: any Error) -> Bool {
        switch error {
        case FinancialError.networkFailure, FinancialError.rateLimitExceeded, FinancialError.invalidResponse, FinancialError.decodingFailed:
            return true
        default:
            return false
        }
    }
}
