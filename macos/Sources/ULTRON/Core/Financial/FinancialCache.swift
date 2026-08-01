import Foundation

/// A TTL-based cache for financial data.
///
/// Cache entries expire after a configurable duration.
/// Thread-safe via actor isolation.
public actor FinancialCache<Key: Hashable & Sendable, Value: Sendable> {

    private struct Entry {
        let value: Value
        let expiresAt: Date
    }

    private var storage: [Key: Entry] = [:]
    private let defaultTTL: TimeInterval
    private(set) var hits = 0
    private(set) var misses = 0

    public init(defaultTTL: TimeInterval = 60) {
        self.defaultTTL = defaultTTL
    }

    /// Returns a cached value if present and not expired.
    public func get(_ key: Key) -> Value? {
        guard let entry = storage[key] else { misses += 1; return nil }
        guard Date() < entry.expiresAt else { storage[key] = nil; misses += 1; return nil }
        hits += 1
        return entry.value
    }

    /// Stores a value with an optional per-entry TTL.
    public func set(_ key: Key, value: Value, ttl: TimeInterval? = nil) {
        storage[key] = Entry(value: value, expiresAt: Date().addingTimeInterval(ttl ?? defaultTTL))
    }

    /// Removes all entries.
    public func clear() { storage.removeAll(); hits = 0; misses = 0 }

    /// Current number of cached entries.
    public var count: Int { storage.count }

    /// Hit ratio (0.0–1.0).
    public var hitRatio: Double {
        let total = hits + misses
        return total > 0 ? Double(hits) / Double(total) : 0
    }
}
