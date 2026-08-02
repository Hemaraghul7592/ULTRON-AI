/// Tracks the capabilities, markets, and exchanges supported by
/// registered financial providers.
///
/// Queried by `FinancialEngine` before routing a request to determine
/// which provider can handle it.
public struct FinancialRegistry: Sendable {

    private var entries: [Entry] = []

    private struct Entry: Sendable {
        let providerID: String
        let capabilities: Set<FinancialCapability>
        let supportedExchanges: Set<String>
        let supportedSymbols: Set<String>
        let priority: Int
        let enabled: Bool
    }

    // MARK: - Registration

    /// Registers a provider's capabilities.
    public mutating func register(
        providerID: String,
        capabilities: Set<FinancialCapability>,
        exchanges: Set<String> = [],
        symbols: Set<String> = [],
        priority: Int = 0,
        enabled: Bool = true
    ) {
        entries.removeAll { $0.providerID == providerID }
        entries.append(Entry(providerID: providerID, capabilities: capabilities, supportedExchanges: exchanges, supportedSymbols: symbols, priority: priority, enabled: enabled))
        entries.sort { $0.priority < $1.priority }
    }

    /// Removes a provider from the registry.
    public mutating func unregister(providerID: String) {
        entries.removeAll { $0.providerID == providerID }
    }

    // MARK: - Query

    /// Returns provider IDs that support the given capability, sorted by priority.
    public func providers(for capability: FinancialCapability) -> [String] {
        entries.filter { $0.capabilities.contains(capability) }.map(\.providerID)
    }

    /// Whether a registered provider is enabled for routing.
    public func isEnabled(providerID: String) -> Bool {
        entries.first { $0.providerID == providerID }?.enabled ?? false
    }

    /// Returns provider IDs that support the given symbol.
    public func providers(forSymbol symbol: String) -> [String] {
        entries.filter { $0.supportedSymbols.isEmpty || $0.supportedSymbols.contains(symbol) }.map(\.providerID)
    }

    /// Returns provider IDs that support the given exchange.
    public func providers(forExchange exchange: String) -> [String] {
        entries.filter { $0.supportedExchanges.isEmpty || $0.supportedExchanges.contains(exchange) }.map(\.providerID)
    }

    /// All registered provider IDs in priority order.
    public var registeredProviderIDs: [String] { entries.map(\.providerID) }

    /// Number of registered providers.
    public var count: Int { entries.count }
}
