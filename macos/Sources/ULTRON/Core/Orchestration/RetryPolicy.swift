import Foundation

/// Configurable retry behavior for provider requests.
///
/// Supports exponential backoff with optional jitter to prevent
/// thundering herd problems when multiple requests retry simultaneously.
public struct RetryPolicy: Sendable {

    // MARK: - Properties

    /// Maximum number of execution attempts. Must be >= 1.
    public let maxAttempts: Int

    /// Delay before the first retry, in seconds.
    public let baseDelay: TimeInterval

    /// Maximum delay between retries, in seconds. Caps the exponential
    /// backoff calculation.
    public let maxDelay: TimeInterval

    /// Backoff multiplier. Each retry's delay is multiplied by this
    /// value raised to the attempt number.
    public let backoffMultiplier: Double

    /// Whether to add random jitter (0–25% of calculated delay).
    public let useJitter: Bool

    // MARK: - Initialization

    public init(
        maxAttempts: Int = 3,
        baseDelay: TimeInterval = 0.5,
        maxDelay: TimeInterval = 30.0,
        backoffMultiplier: Double = 2.0,
        useJitter: Bool = true
    ) {
        self.maxAttempts = max(1, maxAttempts)
        self.baseDelay = max(0, baseDelay)
        self.maxDelay = max(baseDelay, maxDelay)
        self.backoffMultiplier = max(1.0, backoffMultiplier)
        self.useJitter = useJitter
    }

    // MARK: - Presets

    /// Fast retry: 2 attempts, 100ms base, 1s max.
    public static let fast = RetryPolicy(maxAttempts: 2, baseDelay: 0.1, maxDelay: 1.0)

    /// Standard: 3 attempts, 500ms base, 10s max. Default.
    public static let standard = RetryPolicy(maxAttempts: 3, baseDelay: 0.5, maxDelay: 10.0)

    /// Resilient: 5 attempts, 1s base, 60s max.
    public static let resilient = RetryPolicy(maxAttempts: 5, baseDelay: 1.0, maxDelay: 60.0)

    /// No retries: 1 attempt.
    public static let noRetry = RetryPolicy(maxAttempts: 1, baseDelay: 0, maxDelay: 0)

    // MARK: - Delay Calculation

    /// Calculates the delay before the nth retry attempt.
    ///
    /// - Parameter attempt: The 0-based attempt index.
    /// - Returns: The delay in seconds.
    func delay(forAttempt attempt: Int) -> TimeInterval {
        let exponential = baseDelay * pow(backoffMultiplier, Double(attempt))
        let capped = min(exponential, maxDelay)
        guard useJitter else { return capped }
        let jitter = Double.random(in: 0...(capped * 0.25))
        return capped + jitter
    }
}
