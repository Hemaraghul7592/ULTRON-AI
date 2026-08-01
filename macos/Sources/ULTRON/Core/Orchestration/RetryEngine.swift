import Foundation

/// Executes an operation with configurable retry behavior.
///
/// `RetryEngine` is stateless. It receives a policy and an async closure,
/// executes the closure up to `maxAttempts` times, and applies backoff
/// delays between retries.
///
/// The engine does NOT decide whether to retry based on error type —
/// that decision belongs to the orchestrator. If the closure throws,
/// the engine retries unconditionally up to the attempt limit.
public struct RetryEngine: Sendable {

    /// Executes the given operation with retry.
    ///
    /// - Parameters:
    ///   - policy: The retry policy to apply.
    ///   - operation: The async closure to execute.
    /// - Returns: The result of a successful execution.
    /// - Throws: The error from the final failed attempt, wrapped in
    ///   `OrchestrationError.retriesExhausted` if all attempts fail.
    ///
    /// If the closure succeeds on the first attempt, no delay is applied
    /// and the result is returned immediately.
    public func execute<T: Sendable>(
        with policy: RetryPolicy,
        operation: @Sendable () async throws -> T
    ) async throws -> T {
        var lastError: any Error = OrchestrationError.retriesExhausted(
            providerID: "unknown",
            attempts: policy.maxAttempts,
            underlying: CancellationError()
        )

        for attempt in 0..<policy.maxAttempts {
            if attempt > 0 {
                let delay = policy.delay(forAttempt: attempt - 1)
                try await Task.sleep(for: .seconds(delay))
            }

            do {
                return try await operation()
            } catch {
                lastError = error
            }
        }

        throw lastError
    }
}
