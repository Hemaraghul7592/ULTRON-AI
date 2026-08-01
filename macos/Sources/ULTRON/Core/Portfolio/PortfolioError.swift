public enum PortfolioError: Error, CustomStringConvertible {
    case notFound(String)
    case insufficientCash(required: Double, available: Double)
    case insufficientHoldings(symbol: String, required: Double, available: Double)
    case duplicateSymbol(String)
    case invalidOperation(String)

    public var description: String {
        switch self {
        case .notFound(let m): "Not found: \(m)"
        case .insufficientCash(let r, let a): "Insufficient cash: need \(r), have \(a)"
        case .insufficientHoldings(let s, let r, let a): "Insufficient \(s): need \(r), have \(a)"
        case .duplicateSymbol(let s): "Duplicate symbol: \(s)"
        case .invalidOperation(let m): "Invalid operation: \(m)"
        }
    }
}
