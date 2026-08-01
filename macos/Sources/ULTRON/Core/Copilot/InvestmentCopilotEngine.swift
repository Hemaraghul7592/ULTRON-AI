import Foundation

/// Autonomous Investment Copilot — combines all engines for investment intelligence.
@MainActor
public final class InvestmentCopilotEngine {

    private let logger: Logger
    private var goals: [InvestmentGoal] = []
    public weak var advisorEngine: AIAdvisorEngine?
    public weak var alertEngine: AlertEngine?

    public init(logger: Logger) { self.logger = logger }

    // MARK: - Investment Scoring

    public func scoreSymbol(symbol: String, rsi: Double? = nil, macdBullish: Bool = false, aboveMA: Bool = false,
                             revenueGrowth: Double? = nil, netMargin: Double? = nil, healthScore: Double? = nil,
                             pe: Double? = nil, pb: Double? = nil, promoterBuying: Bool = false, recentFilings: Int = 0) -> InvestmentScore {
        InvestmentScoringEngine.overallScore(symbol: symbol, rsi: rsi, macdBullish: macdBullish, aboveMA: aboveMA,
            revenueGrowth: revenueGrowth, netMargin: netMargin, healthScore: healthScore,
            pe: pe, pb: pb, promoterBuying: promoterBuying, recentFilings: recentFilings)
    }

    public func scoreMultiple(stocks: [(symbol: String, rsi: Double?, pe: Double?)]) -> [InvestmentScore] {
        stocks.map { scoreSymbol(symbol: $0.symbol, rsi: $0.rsi, pe: $0.pe) }.sorted { $0.overall > $1.overall }
    }

    // MARK: - Portfolio Review

    public func reviewPortfolio(summary: PortfolioSummary, scores: [InvestmentScore]) -> PortfolioReview {
        var recs: [InvestmentRecommendation] = []
        let poorPerformers = scores.filter { $0.overall < 40 }
        let strongPerformers = scores.filter { $0.overall >= 70 }

        for s in poorPerformers { recs.append(InvestmentRecommendation(symbol: s.symbol, action: .reduce, reasoning: "Low overall score (\(Int(s.overall)))", confidence: 0.6, signals: ["Technical: \(Int(s.technical))", "Fundamental: \(Int(s.fundamental))"])) }
        for s in strongPerformers { recs.append(InvestmentRecommendation(symbol: s.symbol, action: .increase, reasoning: "Strong overall score (\(Int(s.overall)))", confidence: 0.7, signals: ["Technical: \(Int(s.technical))", "Fundamental: \(Int(s.fundamental))"])) }
        if summary.holdingsCount <= 2 { recs.append(InvestmentRecommendation(symbol: "PORTFOLIO", action: .researchFurther, reasoning: "Low diversification — only \(summary.holdingsCount) holdings", confidence: 0.8)) }

        let divScore = PortfolioCalculator.diversificationScore(holdings: scores.map { ($0.symbol, Double($0.overall)) })
        let riskScore = 100 - max(0, min(100, abs(summary.totalReturnPercent) * 2.5))

        return PortfolioReview(allocationScore: 50 + (summary.cashBalance / max(summary.totalValue, 1) > 0.2 ? -15 : 10), diversificationScore: divScore, riskScore: riskScore, recommendations: recs, summary: "Portfolio reviewed with \(recs.count) recommendations.")
    }

    // MARK: - Scenario Analysis

    public func simulateScenario(_ scenario: String, currentValue: Double, currentCash: Double, change: Double, holdings: [(symbol: String, value: Double)]) -> ScenarioResult {
        let projectedValue = currentValue * (1 + change)
        let projectedReturn = (projectedValue - currentValue) / currentValue * 100
        let total = holdings.reduce(0) { $0 + $1.value } + currentCash
            let newAlloc = holdings.map { AllocationItem(symbol: $0.symbol, percent: $0.value * (1 + change) / total * 100) }
        let insights = [change > 0 ? "Growth scenario: +\(Int(change * 100))%" : "Decline scenario: \(Int(change * 100))%", "Portfolio value: $\(String(format: "%.0f", projectedValue))"]
        return ScenarioResult(scenario: scenario, projectedValue: projectedValue, projectedReturn: projectedReturn, newAllocation: newAlloc, insights: insights)
    }

    // MARK: - Goal Planner

    public func addGoal(_ goal: InvestmentGoal) { goals.append(goal) }
    public func getGoals() -> [InvestmentGoal] { goals }
    public func updateGoalProgress(id: String, progress: Double) {
        if let idx = goals.firstIndex(where: { $0.id == id }) { goals[idx].currentProgress = min(1, max(0, progress)) }
    }
    public func suggestAllocation(for goal: InvestmentGoal) -> String {
        if goal.riskTolerance > 0.7 { "80% Equity, 15% Debt, 5% Gold" }
        else if goal.riskTolerance > 0.4 { "60% Equity, 30% Debt, 10% Gold" }
        else { "30% Equity, 50% Debt, 20% Gold" }
    }

    // MARK: - Opportunity Scanner

    public func scanOpportunities(quotes: [String: Double], rsiValues: [String: Double], peValues: [String: Double]) -> [InvestmentRecommendation] {
        var results: [InvestmentRecommendation] = []
        for (symbol, _) in quotes {
            let rsi = rsiValues[symbol] ?? 50; let pe = peValues[symbol]
            if rsi < 30 { results.append(InvestmentRecommendation(symbol: symbol, action: .watch, reasoning: "RSI oversold (\(String(format: "%.1f", rsi)))", confidence: 0.6, signals: ["RSI oversold"], sources: ["Technical"])) }
            if let pe, pe < 10 { results.append(InvestmentRecommendation(symbol: symbol, action: .researchFurther, reasoning: "Low P/E (\(String(format: "%.1f", pe)))", confidence: 0.5, signals: ["Low P/E"], sources: ["Fundamental"])) }
        }
        return results
    }

    // MARK: - AI Integration

    public func explainRecommendation(_ rec: InvestmentRecommendation, using advisor: AIAdvisorEngine? = nil) async -> String {
        guard let ai = advisor ?? advisorEngine else { return rec.reasoning }
        let response = await ai.ask(AdvisorRequest(question: "Explain investment recommendation: \(rec.action.rawValue) on \(rec.symbol). Reasoning: \(rec.reasoning)."))
        return response.summary.isEmpty ? rec.reasoning : response.summary
    }
}
