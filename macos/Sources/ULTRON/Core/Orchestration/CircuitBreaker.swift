import Foundation

/// A circuit breaker that protects against cascading provider failures.
///
/// When a provider experiences consecutive failures exceeding the
/// configured threshold, the breaker opens and blocks further requests.
/// After a cooldown period, it transitions to half-open, allowing a
/// single probe request. If the probe succeeds, the breaker closes.
///
/// ## Thread Safety
///
/// `CircuitBreaker` is an actor. All state transitions are serialized.
public actor CircuitBreaker {

    // MARK: - State

    public enum State: Sendable {
        case closed
        case open
        case halfOpen
    }

    // MARK: - Properties

    /// The current state of the breaker.
    public private(set) var state: State = .closed

    /// Number of consecutive failures in the current window.
    public private(set) var failureCount: Int = 0

    /// Number of consecutive successes in the current window.
    public private(set) var successCount: Int = 0

    /// When the breaker opened, for cooldown calculation. Nil when closed.
    private var openedAt: Date?

    // MARK: - Configuration

    private let failureThreshold: Int
    private let cooldownDuration: TimeInterval
    private let recoverySuccesses: Int

    // MARK: - Initialization

    /// Creates a circuit breaker.
    ///
    /// - Parameters:
    ///   - failureThreshold: Consecutive failures before opening. Default 5.
    ///   - cooldownDuration: Seconds to wait before allowing a probe. Default 600.
    ///   - recoverySuccesses: Consecutive successes to close from half-open. Default 1.
    public init(
        failureThreshold: Int = 5,
        cooldownDuration: TimeInterval = 600,
        recoverySuccesses: Int = 1
    ) {
        self.failureThreshold = failureThreshold
        self.cooldownDuration = cooldownDuration
        self.recoverySuccesses = recoverySuccesses
    }

    // MARK: - API

    /// Returns whether a request should be allowed through.
    ///
    /// In `.closed` state, always returns `true`.
    /// In `.open` state, returns `true` only if cooldown has expired
    /// (transitioning to `.halfOpen` in the process).
    /// In `.halfOpen` state, returns `true` (probe request).
    public func allowRequest() -> Bool {
        switch state {
        case .closed:
            return true
        case .open:
            guard let openedAt else {
                state = .closed
                return true
            }
            if Date().timeIntervalSince(openedAt) >= cooldownDuration {
                state = .halfOpen
                return true
            }
            return false
        case .halfOpen:
            return true
        }
    }

    /// Records a successful request.
    ///
    /// In `.halfOpen` state, accumulating enough successes transitions
    /// the breaker back to `.closed`.
    public func recordSuccess() {
        failureCount = 0
        switch state {
        case .closed:
            successCount += 1
        case .halfOpen:
            successCount += 1
            if successCount >= recoverySuccesses {
                state = .closed
                successCount = 0
            }
        case .open:
            break
        }
    }

    /// Records a failed request.
    ///
    /// If the failure threshold is reached, the breaker opens.
    public func recordFailure() {
        successCount = 0
        failureCount += 1
        if failureCount >= failureThreshold {
            state = .open
            openedAt = Date()
        }
    }

    /// Forces the breaker open immediately (manual trip).
    public func forceOpen() {
        state = .open
        openedAt = Date()
    }

    /// Resets the breaker to its initial closed state.
    public func reset() {
        state = .closed
        failureCount = 0
        successCount = 0
        openedAt = nil
    }
}
