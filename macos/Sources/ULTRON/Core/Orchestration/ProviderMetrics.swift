import Foundation

/// Runtime metrics for a single service provider.
///
/// All properties are read and written on `@MainActor` via the
/// orchestrator. The struct itself is `Sendable` so it can be
/// copied for diagnostics without crossing actor boundaries.
public struct ProviderMetrics: Sendable {

    // MARK: - Counts

    public var totalRequests: Int = 0
    public var successfulRequests: Int = 0
    public var failedRequests: Int = 0

    // MARK: - Consecutive Tracking

    public var consecutiveFailures: Int = 0
    public var consecutiveSuccesses: Int = 0

    // MARK: - Timing

    public var totalLatency: TimeInterval = 0
    public var lastRequestAt: Date?
    public var lastSuccessAt: Date?
    public var lastFailureAt: Date?

    // MARK: - Error

    public var lastErrorMessage: String?
    public var cooldownUntil: Date?

    // MARK: - Computed

    /// The fraction of successful requests (0.0–1.0).
    public var availability: Double {
        guard totalRequests > 0 else { return 1.0 }
        return Double(successfulRequests) / Double(totalRequests)
    }

    /// The average request latency in seconds.
    public var averageLatency: TimeInterval {
        guard successfulRequests > 0 else { return 0 }
        return totalLatency / Double(successfulRequests)
    }

    /// Whether the cooldown period has elapsed.
    public var isCooldownExpired: Bool {
        guard let until = cooldownUntil else { return true }
        return Date() >= until
    }

    // MARK: - Mutations

    public mutating func recordSuccess(latency: TimeInterval) {
        totalRequests += 1
        successfulRequests += 1
        consecutiveSuccesses += 1
        consecutiveFailures = 0
        totalLatency += latency
        lastRequestAt = Date()
        lastSuccessAt = Date()
        lastErrorMessage = nil
        cooldownUntil = nil
    }

    public mutating func recordFailure(error: String) {
        totalRequests += 1
        failedRequests += 1
        consecutiveFailures += 1
        consecutiveSuccesses = 0
        lastRequestAt = Date()
        lastFailureAt = Date()
        lastErrorMessage = error
    }

    public mutating func enterCooldown(until: Date) {
        cooldownUntil = until
    }

    public mutating func reset() {
        self = ProviderMetrics()
    }
}
