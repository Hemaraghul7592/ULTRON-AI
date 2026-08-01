/// Errors produced by the Financial module.
public enum FinancialError: Error, CustomStringConvertible {
    case symbolNotFound(String)
    case providerNotAvailable(String)
    case invalidData(String)
    case rateLimitExceeded(String)
    case unsupportedCapability(String)
    case cacheExpired(key: String)

    public var description: String {
        switch self {
        case .symbolNotFound(let s): "Symbol '\(s)' not found."
        case .providerNotAvailable(let p): "Provider '\(p)' is not available."
        case .invalidData(let m): "Invalid data: \(m)"
        case .rateLimitExceeded(let p): "Rate limit exceeded for '\(p)'."
        case .unsupportedCapability(let c): "Capability '\(c)' is not supported."
        case .cacheExpired(let k): "Cache expired for key '\(k)'."
        }
    }
}
