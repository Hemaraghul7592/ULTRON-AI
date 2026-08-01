import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite struct AIAdvisorTests {

    // MARK: - LLM Provider Tests

    @Test("MockLLMProvider returns configured response") func testMockProvider() async throws {
        let mock = MockLLMProvider(response: "Test response")
        let result = try await mock.generate(prompt: "test", systemPrompt: "")
        #expect(result == "Test response")
    }

    @Test("MockLLMProvider health check") func testMockHealth() async {
        let mock = MockLLMProvider()
        #expect(await mock.healthCheck() == true)
    }

    @Test("MockLLMProvider availability") func testMockAvailability() async {
        let mock = MockLLMProvider()
        #expect(await mock.isAvailable == true)
    }

    // MARK: - Prompt Builder Tests

    @Test("PromptBuilder includes portfolio data") func testPromptBuilderPortfolio() {
        let builder = PromptBuilder()
        let summary = PortfolioSummary(totalValue: 50000, totalInvested: 40000, totalReturn: 5000, totalReturnPercent: 12.5, cashBalance: 5000, holdingsCount: 5, dayChange: 200, dayChangePercent: 0.4, topHolding: "AAPL", worstHolding: "TSLA")
        let request = AdvisorRequest(question: "How is my portfolio?", portfolioSnapshot: summary)
        let (_, user) = builder.build(request)
        #expect(user.contains("50000"))
        #expect(user.contains("12.5"))
    }

    @Test("PromptBuilder includes news") func testPromptBuilderNews() {
        let builder = PromptBuilder()
        let news = [NewsArticle(title: "Market rally continues", source: "Reuters")]
        let request = AdvisorRequest(question: "What's happening?", news: news)
        let (_, user) = builder.build(request)
        #expect(user.contains("Market rally"))
    }

    @Test("PromptBuilder includes economic context") func testPromptBuilderEconomic() {
        let builder = PromptBuilder()
        let request = AdvisorRequest(question: "Explain inflation", economicContext: "CPI: 3.2%, GDP: 2.8%")
        let (_, user) = builder.build(request)
        #expect(user.contains("CPI"))
    }

    // MARK: - Conversation Memory Tests

    @Test("ConversationMemory stores entries") func testMemoryStore() async {
        let memory = ConversationMemory(maxEntries: 5)
        await memory.add(role: .user, content: "Hello")
        await memory.add(role: .assistant, content: "Hi there")
        let entries = await memory.recent()
        #expect(entries.count == 2)
        #expect(entries[0].role == .user)
        #expect(entries[1].role == .assistant)
    }

    @Test("ConversationMemory respects max entries") func testMemoryMax() async {
        let memory = ConversationMemory(maxEntries: 3)
        for i in 0..<5 { await memory.add(role: .user, content: "msg\(i)") }
        let entries = await memory.recent()
        #expect(entries.count == 3)
    }

    @Test("ConversationMemory clears") func testMemoryClear() async {
        let memory = ConversationMemory()
        await memory.add(role: .user, content: "test")
        await memory.clear()
        #expect(await memory.count == 0)
    }

    // MARK: - Recommendation Tests

    @Test("Recommendations for low diversification") func testRecommendDiversification() {
        let summary = PortfolioSummary(totalValue: 10000, totalInvested: 10000, totalReturn: 0, totalReturnPercent: 0, cashBalance: 1000, holdingsCount: 1, dayChange: 0, dayChangePercent: 0, topHolding: "AAPL", worstHolding: nil)
        let recs = RecommendationEngine.analyze(portfolio: summary)
        #expect(recs.contains { $0.type == .diversification })
    }

    @Test("Recommendations for high cash") func testRecommendHighCash() {
        let summary = PortfolioSummary(totalValue: 20000, totalInvested: 5000, totalReturn: 0, totalReturnPercent: 0, cashBalance: 15000, holdingsCount: 3, dayChange: 0, dayChangePercent: 0, topHolding: "AAPL", worstHolding: nil)
        let recs = RecommendationEngine.analyze(portfolio: summary)
        #expect(recs.contains { $0.type == .allocation })
    }

    @Test("Recommendations for drawdown") func testRecommendDrawdown() {
        let summary = PortfolioSummary(totalValue: 8000, totalInvested: 10000, totalReturn: -2000, totalReturnPercent: -20, cashBalance: 1000, holdingsCount: 4, dayChange: -100, dayChangePercent: -1.2, topHolding: "AAPL", worstHolding: "TSLA")
        let recs = RecommendationEngine.analyze(portfolio: summary)
        #expect(recs.contains { $0.type == .warning })
    }

    // MARK: - AI Advisor Engine Tests

    @Test("AIAdvisorEngine uses primary provider") func testEnginePrimary() async {
        let engine = AIAdvisorEngine(primary: MockLLMProvider(response: "Primary response"), fallback: MockLLMProvider(response: "Fallback"), logger: Logger(configuration: .init(minimumLevel: .error)))
        let response = await engine.ask(AdvisorRequest(question: "Test"))
        #expect(response.summary == "Primary response")
        #expect(response.provider == "Mock")
    }

    @Test("AIAdvisorEngine falls back when primary unavailable") func testEngineFallback() async {
        let primary = MockLLMProvider(response: "Primary")
        await primary.setAvailable(false)
        let fallback = MockLLMProvider(response: "Fallback response")
        let engine = AIAdvisorEngine(primary: primary, fallback: fallback, logger: Logger(configuration: .init(minimumLevel: .error)))
        let response = await engine.ask(AdvisorRequest(question: "Test"))
        #expect(response.provider == "Mock")
    }

    @Test("AIAdvisorEngine returns fallback when all unavailable") func testEngineAllUnavailable() async {
        let p1 = MockLLMProvider(); await p1.setAvailable(false)
        let p2 = MockLLMProvider(); await p2.setAvailable(false)
        let engine = AIAdvisorEngine(primary: p1, fallback: p2, logger: Logger(configuration: .init(minimumLevel: .error)))
        let response = await engine.ask(AdvisorRequest(question: "Test"))
        #expect(response.provider == "none")
        #expect(response.summary.contains("unable"))
    }

    @Test("AIAdvisorEngine generates recommendations") func testEngineRecommend() {
        let engine = AIAdvisorEngine(primary: MockLLMProvider(), fallback: MockLLMProvider(), logger: Logger(configuration: .init(minimumLevel: .error)))
        let summary = PortfolioSummary(totalValue: 10000, totalInvested: 10000, totalReturn: 0, totalReturnPercent: 0, cashBalance: 1000, holdingsCount: 1, dayChange: 0, dayChangePercent: 0, topHolding: "AAPL", worstHolding: nil)
        let recs = engine.recommend(portfolio: summary)
        #expect(!recs.isEmpty)
    }

    @Test("AIAdvisorEngine health check") func testEngineHealth() async {
        let engine = AIAdvisorEngine(primary: MockLLMProvider(), fallback: MockLLMProvider(), logger: Logger(configuration: .init(minimumLevel: .error)))
        let (p, f) = await engine.healthCheck()
        #expect(p == true)
        #expect(f == true)
    }

    @Test("AIAdvisorEngine conversation history") func testEngineHistory() async {
        let engine = AIAdvisorEngine(primary: MockLLMProvider(response: "Hello!"), fallback: MockLLMProvider(), logger: Logger(configuration: .init(minimumLevel: .error)))
        _ = await engine.ask(AdvisorRequest(question: "Hi"))
        let history = await engine.getHistory()
        #expect(history.count == 2)
        #expect(history[0].role == .user)
        #expect(history[1].role == .assistant)
    }

    @Test("AIAdvisorEngine clear history") func testEngineClearHistory() async {
        let engine = AIAdvisorEngine(primary: MockLLMProvider(response: "Hi"), fallback: MockLLMProvider(), logger: Logger(configuration: .init(minimumLevel: .error)))
        _ = await engine.ask(AdvisorRequest(question: "Test"))
        await engine.clearHistory()
        #expect(await engine.getHistory().isEmpty)
    }
}
