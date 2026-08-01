/// Errors produced by the Technical Analysis engine.
public enum TAError: Error, CustomStringConvertible {
    case insufficientData(required: Int, available: Int)
    case invalidPeriod(String)
    case calculationFailed(String)

    public var description: String {
        switch self {
        case .insufficientData(let r, let a): "Need \(r) data points, got \(a)."
        case .invalidPeriod(let m): "Invalid period: \(m)"
        case .calculationFailed(let m): "Calculation failed: \(m)"
        }
    }
}

/// Configuration for the Technical Analysis engine.
public struct TAConfig: Sendable {
    public let defaultSMAPeriods: [Int]
    public let defaultEMAPeriods: [Int]
    public let defaultRSIPeriod: Int
    public let defaultMACDFast: Int
    public let defaultMACDSlow: Int
    public let defaultMACDSignal: Int
    public let defaultBBPeriod: Int
    public let defaultBBMultiplier: Double
    public let defaultATRPeriod: Int
    public let defaultStochasticK: Int
    public let defaultStochasticD: Int
    public let cacheEnabled: Bool

    public init(
        defaultSMAPeriods: [Int] = [20, 50, 200],
        defaultEMAPeriods: [Int] = [12, 26],
        defaultRSIPeriod: Int = 14,
        defaultMACDFast: Int = 12, defaultMACDSlow: Int = 26, defaultMACDSignal: Int = 9,
        defaultBBPeriod: Int = 20, defaultBBMultiplier: Double = 2.0,
        defaultATRPeriod: Int = 14,
        defaultStochasticK: Int = 14, defaultStochasticD: Int = 3,
        cacheEnabled: Bool = true
    ) {
        self.defaultSMAPeriods = defaultSMAPeriods
        self.defaultEMAPeriods = defaultEMAPeriods
        self.defaultRSIPeriod = defaultRSIPeriod
        self.defaultMACDFast = defaultMACDFast; self.defaultMACDSlow = defaultMACDSlow; self.defaultMACDSignal = defaultMACDSignal
        self.defaultBBPeriod = defaultBBPeriod; self.defaultBBMultiplier = defaultBBMultiplier
        self.defaultATRPeriod = defaultATRPeriod
        self.defaultStochasticK = defaultStochasticK; self.defaultStochasticD = defaultStochasticD
        self.cacheEnabled = cacheEnabled
    }

    public static let `default` = TAConfig()
}
