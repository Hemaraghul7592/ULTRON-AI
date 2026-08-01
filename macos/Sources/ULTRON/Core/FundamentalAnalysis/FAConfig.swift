/// Errors for the Fundamental Analysis engine.
public enum FAError: Error, CustomStringConvertible {
    case missingStatement(String)
    case insufficientData(String)
    case divisionByZero(String)
    case negativeEarnings(String)
    case invalidAssumption(String)

    public var description: String {
        switch self {
        case .missingStatement(let m): "Missing statement: \(m)"
        case .insufficientData(let m): "Insufficient data: \(m)"
        case .divisionByZero(let m): "Division by zero: \(m)"
        case .negativeEarnings(let m): "Negative earnings: \(m)"
        case .invalidAssumption(let m): "Invalid assumption: \(m)"
        }
    }
}

/// Configuration for the Fundamental Analysis engine.
public struct FAConfig: Sendable {
    public let riskFreeRate: Double; public let marketReturn: Double; public let terminalGrowthRate: Double
    public let projectionYears: Int; public let defaultDiscountRate: Double

    public init(riskFreeRate: Double = 0.04, marketReturn: Double = 0.10, terminalGrowthRate: Double = 0.025, projectionYears: Int = 5, defaultDiscountRate: Double = 0.10) {
        self.riskFreeRate = riskFreeRate; self.marketReturn = marketReturn
        self.terminalGrowthRate = terminalGrowthRate; self.projectionYears = projectionYears
        self.defaultDiscountRate = defaultDiscountRate
    }
    public static let `default` = FAConfig()
}
