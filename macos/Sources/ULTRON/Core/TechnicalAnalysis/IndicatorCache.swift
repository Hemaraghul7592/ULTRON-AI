import Foundation

/// Actor-based cache for indicator results.
///
/// Caches computed indicators by (symbol, indicator, parameters) key
/// to avoid redundant calculations.
public actor IndicatorCache {
    private var storage: [String: any Sendable] = [:]
    private(set) var hits = 0
    private(set) var misses = 0

    public init() {}

    public func get<T: Sendable>(_ key: String) -> T? {
        if let v = storage[key] as? T { hits += 1; return v }
        misses += 1; return nil
    }

    public func set<T: Sendable>(_ key: String, value: T) {
        storage[key] = value
    }

    public func clear() { storage.removeAll(); hits = 0; misses = 0 }

    public var count: Int { storage.count }
}
