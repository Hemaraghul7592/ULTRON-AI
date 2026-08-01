import Foundation

/// Errors produced by the service orchestration layer.
///
/// All errors are provider-agnostic. Provider names appear only in
/// internal logging, never in user-facing messages.
public enum OrchestrationError: Error, CustomStringConvertible {

    /// All configured providers for this category have been exhausted.
    /// No provider is currently healthy or available.
    case allProvidersExhausted(category: ServiceCategory, attempted: [String])

    /// No provider supports the requested capability.
    case noProviderForCapability(ServiceCapability, category: ServiceCategory)

    /// A provider's health check indicates it cannot serve requests.
    case providerUnhealthy(providerID: String, reason: String)

    /// All retry attempts failed. The underlying error is preserved.
    case retriesExhausted(providerID: String, attempts: Int, underlying: any Error)

    /// The circuit breaker is open; the provider is in cooldown.
    case circuitBreakerOpen(providerID: String, retryAfter: TimeInterval)

    // MARK: - CustomStringConvertible

    public var description: String {
        switch self {
        case .allProvidersExhausted(let category, _):
            return "All \(category.rawValue) providers are currently unavailable."
        case .noProviderForCapability(let cap, let category):
            return "No \(category.rawValue) provider supports capability '\(cap.rawValue)'."
        case .providerUnhealthy(let id, let reason):
            return "Provider '\(id)' is unhealthy: \(reason)"
        case .retriesExhausted(let id, let attempts, _):
            return "Provider '\(id)' failed after \(attempts) attempts."
        case .circuitBreakerOpen(let id, let retryAfter):
            return "Provider '\(id)' is temporarily unavailable (retry in \(Int(retryAfter))s)."
        }
    }
}
