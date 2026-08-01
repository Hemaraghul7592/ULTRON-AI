import Foundation

// MARK: - Recommendation

public struct InvestmentRecommendation: Sendable, Codable, Identifiable {
    public let id: String; public let symbol: String; public let action: RecommendationAction
    public let reasoning: String; public let confidence: Double; public let signals: [String]
    public let risks: [String]; public let opportunities: [String]; public let sources: [String]
    public let timestamp: Date

    public init(id: String = UUID().uuidString, symbol: String, action: RecommendationAction, reasoning: String = "", confidence: Double = 0, signals: [String] = [], risks: [String] = [], opportunities: [String] = [], sources: [String] = [], timestamp: Date = Date()) {
        self.id = id; self.symbol = symbol; self.action = action; self.reasoning = reasoning; self.confidence = confidence
        self.signals = signals; self.risks = risks; self.opportunities = opportunities; self.sources = sources; self.timestamp = timestamp
    }
}

public enum RecommendationAction: String, Sendable, Codable, CaseIterable {
    case increase, reduce, hold, watch, avoid, researchFurther
}

// MARK: - Investment Score

public struct InvestmentScore: Sendable, Codable {
    public let symbol: String
    public let technical: Double; public let fundamental: Double; public let risk: Double
    public let momentum: Double; public let valuation: Double; public let sentiment: Double
    public let overall: Double; public let timestamp: Date

    public init(symbol: String, technical: Double = 50, fundamental: Double = 50, risk: Double = 50, momentum: Double = 50, valuation: Double = 50, sentiment: Double = 50, timestamp: Date = Date()) {
        self.symbol = symbol; self.technical = technical; self.fundamental = fundamental; self.risk = risk
        self.momentum = momentum; self.valuation = valuation; self.sentiment = sentiment
        overall = (technical * 0.25 + fundamental * 0.25 + risk * 0.15 + momentum * 0.15 + valuation * 0.10 + sentiment * 0.10)
        self.timestamp = timestamp
    }

    public enum Rating: String, Sendable { case strong, good, neutral, weak }
    public var rating: Rating {
        if overall >= 75 { .strong } else if overall >= 55 { .good } else if overall >= 35 { .neutral } else { .weak }
    }
}

// MARK: - Portfolio Review

public struct PortfolioReview: Sendable, Codable {
    public let allocationScore: Double; public let diversificationScore: Double; public let riskScore: Double
    public let recommendations: [InvestmentRecommendation]; public let summary: String; public let timestamp: Date

    public init(allocationScore: Double = 50, diversificationScore: Double = 50, riskScore: Double = 50, recommendations: [InvestmentRecommendation] = [], summary: String = "", timestamp: Date = Date()) {
        self.allocationScore = allocationScore; self.diversificationScore = diversificationScore; self.riskScore = riskScore
        self.recommendations = recommendations; self.summary = summary; self.timestamp = timestamp
    }
}

// MARK: - Scenario

public struct AllocationItem: Sendable, Codable {
    public let symbol: String; public let percent: Double
    public init(symbol: String, percent: Double) { self.symbol = symbol; self.percent = percent }
}

public struct ScenarioResult: Sendable, Codable {
    public let scenario: String; public let projectedValue: Double; public let projectedReturn: Double
    public let newAllocation: [AllocationItem]; public let riskChange: Double
    public let insights: [String]

    public init(scenario: String, projectedValue: Double = 0, projectedReturn: Double = 0, newAllocation: [AllocationItem] = [], riskChange: Double = 0, insights: [String] = []) {
        self.scenario = scenario; self.projectedValue = projectedValue; self.projectedReturn = projectedReturn
        self.newAllocation = newAllocation; self.riskChange = riskChange; self.insights = insights
    }
}

// MARK: - Goal

public struct InvestmentGoal: Sendable, Codable, Identifiable {
    public let id: String; public let name: String; public let type: GoalType; public let targetAmount: Double
    public let targetDate: Date; public let riskTolerance: Double; public var currentProgress: Double; public var suggestedAllocation: String

    public init(id: String = UUID().uuidString, name: String, type: GoalType = .wealthCreation, targetAmount: Double, targetDate: Date, riskTolerance: Double = 0.5) {
        self.id = id; self.name = name; self.type = type; self.targetAmount = targetAmount; self.targetDate = targetDate
        self.riskTolerance = riskTolerance; currentProgress = 0; suggestedAllocation = ""
    }

    public var monthsRemaining: Int { max(0, Int(targetDate.timeIntervalSinceNow / 2_629_746)) }
    public var monthlyRequired: Double { monthsRemaining > 0 ? (targetAmount - targetAmount * currentProgress) / Double(monthsRemaining) : 0 }
}

public enum GoalType: String, Sendable, Codable, CaseIterable {
    case wealthCreation, retirement, passiveIncome, education, housePurchase, emergencyFund, custom
}
