/// Errors produced by the Financial module.
public enum FinancialError: Error, CustomStringConvertible {
    case symbolNotFound(String)
    case providerNotAvailable(String)
    case providerFailures(capability: String, failures: [String])
    case invalidData(String)
    case invalidResponse(String)
    case emptyResponse(String)
    case decodingFailed(String)
    case networkFailure(String)
    case rateLimitExceeded(String)
    case unsupportedCapability(String)
    case cacheExpired(key: String)

    public var description: String {
        switch self {
        case .symbolNotFound(let s): "Symbol '\(s)' not found."
        case .providerNotAvailable(let p): "Provider '\(p)' is not available."
        case .providerFailures(let capability, _): "All providers failed for capability '\(capability)'."
        case .invalidData(let m): "Invalid data: \(m)"
        case .invalidResponse(let m): "Invalid response: \(m)"
        case .emptyResponse(let p): "Empty response from '\(p)'."
        case .decodingFailed(let p): "Response decoding failed for '\(p)'."
        case .networkFailure(let p): "Network request failed for '\(p)'."
        case .rateLimitExceeded(let p): "Rate limit exceeded for '\(p)'."
        case .unsupportedCapability(let c): "Capability '\(c)' is not supported."
        case .cacheExpired(let k): "Cache expired for key '\(k)'."
        }
    }
}
