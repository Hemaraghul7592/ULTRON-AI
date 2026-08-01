import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite struct InvestmentCopilotTests {

    // MARK: - Scoring

    @Test("Technical score with RSI 75 is lower") func testTechnicalOverbought() {
        let score = InvestmentScoringEngine.technicalScore(rsi: 75, macdBullish: false, aboveMA: false)
        #expect(score < 50)
    }

    @Test("Technical score with RSI 25 is higher") func testTechnicalOversold() {
        let score = InvestmentScoringEngine.technicalScore(rsi: 25, macdBullish: false, aboveMA: false)
        #expect(score > 50)
    }

    @Test("Fundamental score with strong growth") func testFundamentalStrong() {
        let score = InvestmentScoringEngine.fundamentalScore(revenueGrowth: 0.3, netMargin: 0.25, healthScore: 80)
        #expect(score > 70)
    }

    @Test("Overall score combines all factors") func testOverallScore() {
        let score = InvestmentScoringEngine.overallScore(symbol: "AAPL", rsi: 60, macdBullish: true, aboveMA: true, revenueGrowth: 0.15, netMargin: 0.20, healthScore: 75, pe: 25, pb: 5)
        #expect(score.overall >= 0 && score.overall <= 100)
        #expect(!score.rating.rawValue.isEmpty)
    }

    @Test("Score rating thresholds") func testScoreRatings() {
        let strong = InvestmentScore(symbol: "A", technical: 80, fundamental: 80, risk: 80, momentum: 80, valuation: 80, sentiment: 80)
        #expect(strong.rating == .strong)
        let weak = InvestmentScore(symbol: "B", technical: 20, fundamental: 20, risk: 20, momentum: 20, valuation: 20, sentiment: 20)
        #expect(weak.rating == .weak)
    }

    // MARK: - Portfolio Review

    @Test("Portfolio review generates recommendations") func testPortfolioReview() {
        let engine = InvestmentCopilotEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let summary = PortfolioSummary(totalValue: 50000, totalInvested: 40000, totalReturn: 10000, totalReturnPercent: 25, cashBalance: 5000, holdingsCount: 1, dayChange: 0, dayChangePercent: 0, topHolding: "AAPL", worstHolding: nil)
        let scores = [InvestmentScore(symbol: "AAPL", technical: 30, fundamental: 30, risk: 30, momentum: 30, valuation: 30, sentiment: 30)]
        let review = engine.reviewPortfolio(summary: summary, scores: scores)
        #expect(!review.recommendations.isEmpty)
        #expect(review.diversificationScore == 0)
    }

    // MARK: - Scenario

    @Test("Scenario analysis projects values") func testScenario() {
        let engine = InvestmentCopilotEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let result = engine.simulateScenario("Market +10%", currentValue: 100000, currentCash: 10000, change: 0.10, holdings: [("AAPL", 50000), ("GOOGL", 40000)])
        #expect(result.projectedValue > 100000)
        #expect(!result.insights.isEmpty)
    }

    @Test("Scenario analysis decline") func testScenarioDecline() {
        let engine = InvestmentCopilotEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let result = engine.simulateScenario("Market -20%", currentValue: 100000, currentCash: 10000, change: -0.20, holdings: [])
        #expect(result.projectedValue < 100000)
        #expect(result.projectedReturn < 0)
    }

    // MARK: - Goals

    @Test("Goal planner calculates monthly required") func testGoalMonthly() {
        let future = Date().addingTimeInterval(13 * 2_629_746)
        let goal = InvestmentGoal(name: "House", type: .housePurchase, targetAmount: 1_000_000, targetDate: future, riskTolerance: 0.6)
        #expect(goal.monthsRemaining >= 12)
        #expect(goal.monthlyRequired > 0)
    }

    @Test("Goal planner suggests allocation by risk") func testGoalAllocation() {
        let engine = InvestmentCopilotEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let goal = InvestmentGoal(name: "Retirement", type: .retirement, targetAmount: 5_000_000, targetDate: Date().addingTimeInterval(20 * 365 * 86400), riskTolerance: 0.8)
        let allocation = engine.suggestAllocation(for: goal)
        #expect(allocation.contains("Equity"))
    }

    @Test("Goal progress update") func testGoalProgress() {
        let engine = InvestmentCopilotEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let goal = InvestmentGoal(name: "Test", targetAmount: 100000, targetDate: Date().addingTimeInterval(86400 * 365))
        engine.addGoal(goal)
        engine.updateGoalProgress(id: goal.id, progress: 0.5)
        #expect(engine.getGoals()[0].currentProgress == 0.5)
    }

    // MARK: - Scanner

    @Test("Opportunity scanner finds oversold") func testScannerOversold() {
        let engine = InvestmentCopilotEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let results = engine.scanOpportunities(quotes: ["AAPL": 150], rsiValues: ["AAPL": 25], peValues: [:])
        #expect(results.contains { $0.action == .watch })
    }

    @Test("Opportunity scanner finds low PE") func testScannerLowPE() {
        let engine = InvestmentCopilotEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let results = engine.scanOpportunities(quotes: ["VALUE": 50], rsiValues: [:], peValues: ["VALUE": 8])
        #expect(results.contains { $0.action == .researchFurther })
    }

    // MARK: - Models

    @Test("InvestmentGoal computes months remaining") func testGoalMonths() {
        let future = Date().addingTimeInterval(7 * 2_629_746)
        let goal = InvestmentGoal(name: "Test", targetAmount: 50000, targetDate: future)
        #expect(goal.monthsRemaining >= 6)
    }

    @Test("ScenarioResult stores allocation") func testScenarioAllocation() {
        let result = ScenarioResult(scenario: "Test", projectedValue: 110000, newAllocation: [AllocationItem(symbol: "AAPL", percent: 60), AllocationItem(symbol: "GOOGL", percent: 40)])
        #expect(result.newAllocation.count == 2)
    }
}
