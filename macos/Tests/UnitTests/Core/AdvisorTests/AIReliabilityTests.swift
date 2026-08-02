import Foundation
import Testing

@testable import ULTRON

private actor RecordingLLMProvider: LLMProvider {
    let providerID: String
    let providerName: String
    private let response: String
    private let delay: Duration
    private let failure: LLMError?
    private var available = true
    private(set) var prompts: [(String, String)] = []
    private(set) var generateCount = 0
    private(set) var cancellationCount = 0
    private(set) var started = false

    init(id: String, response: String = "response", delay: Duration = .zero, failure: LLMError? = nil) {
        providerID = id
        providerName = id
        self.response = response
        self.delay = delay
        self.failure = failure
    }

    func setAvailable(_ value: Bool) { available = value }
    var isAvailable: Bool { available }

    func generate(prompt: String, systemPrompt: String) async throws -> String {
        started = true
        generateCount += 1
        prompts.append((prompt, systemPrompt))
        do {
            if delay != .zero { try await Task.sleep(for: delay) }
            try Task.checkCancellation()
            if let failure { throw failure }
            return response
        } catch is CancellationError {
            cancellationCount += 1
            throw CancellationError()
        }
    }

    func healthCheck() async -> Bool { available }
}

@MainActor
@Suite struct AIReliabilityTests {
    @Test("Cancellation propagates through the advisor engine")
    func cancellationPropagates() async {
        let provider = RecordingLLMProvider(id: "slow", delay: .seconds(10))
        let engine = makeEngine(primary: provider, fallback: RecordingLLMProvider(id: "fallback"))
        let task = Task { @MainActor in
            try await engine.askCancellable(AdvisorRequest(question: "Cancel this"))
        }

        while await !provider.started { await Task.yield() }
        task.cancel()
        do {
            _ = try await task.value
            Issue.record("Expected cancellation")
        } catch is CancellationError {
            #expect(await provider.cancellationCount == 1)
        } catch { Issue.record("Unexpected error: \(error)") }

        let history = await engine.getHistory()
        #expect(history.count == 2)
        #expect(history[1].content.contains("cancelled"))
    }

    @Test("Workspace cancellation reaches the provider")
    func workspaceCancellationPropagates() async {
        let provider = RecordingLLMProvider(id: "workspace-slow", delay: .seconds(10))
        let fallback = RecordingLLMProvider(id: "workspace-fallback")
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let memory = ConversationMemory()
        let advisor = makeEngine(primary: provider, fallback: fallback, memory: memory, logger: logger)
        let viewModel = AIWorkspaceViewModel(
            advisorEngine: advisor,
            financialEngine: FinancialEngine(logger: logger),
            portfolioEngine: PortfolioEngine(storage: InMemoryStorage(), logger: logger),
            technicalEngine: TechnicalAnalysisEngine(),
            fundamentalEngine: FundamentalAnalysisEngine(),
            visualizationEngine: VisualizationEngine(logger: logger),
            alertEngine: AlertEngine(logger: logger),
            conversationMemory: memory
        )
        let task = Task { @MainActor in await viewModel.send(question: "Cancel workspace request") }

        while !(await provider.started) { await Task.yield() }
        viewModel.cancel()
        await task.value
        #expect(viewModel.state == .cancelled)
        #expect(await provider.cancellationCount == 1)
    }

    @Test("Primary failure falls back with the original prompt")
    func fallbackPreservesPrompt() async {
        let primary = RecordingLLMProvider(id: "primary", failure: .unavailable("failed"))
        let fallback = RecordingLLMProvider(id: "fallback", response: "fallback response")
        let engine = makeEngine(primary: primary, fallback: fallback)
        let request = AdvisorRequest(question: "Explain the risk", economicContext: "CPI: 3.2%")

        let response = await engine.ask(request)
        #expect(response.provider == "fallback")
        #expect(await primary.generateCount == 1)
        #expect(await fallback.generateCount == 1)
        #expect(await primary.prompts[0].0 == fallback.prompts[0].0)
        #expect(await primary.prompts[0].1 == fallback.prompts[0].1)
    }

    @Test("Retry preserves prompt and context in a new ordered turn")
    func retryPreservesRequest() async throws {
        let provider = RecordingLLMProvider(id: "provider", response: "stable")
        let engine = makeEngine(primary: provider, fallback: RecordingLLMProvider(id: "fallback"))
        let request = AdvisorRequest(question: "Review my portfolio", economicContext: "GDP: 2.8%")

        _ = try await engine.askCancellable(request)
        _ = try await engine.retryCancellable(request)
        #expect(await provider.generateCount == 2)
        #expect(await provider.prompts[0].0 == provider.prompts[1].0)
        #expect(await provider.prompts[0].1 == provider.prompts[1].1)
        #expect((await engine.getHistory()).count == 4)
    }

    @Test("Concurrent memory turns remain complete and ordered")
    func concurrentTurns() async {
        let memory = ConversationMemory()
        await withTaskGroup(of: ConversationMemory.Turn.self) { group in
            for index in 0..<20 {
                group.addTask { await memory.beginTurn(question: "Question \(index)") }
            }
            for await turn in group {
                await memory.update(id: turn.assistantEntryID, content: "Answer")
            }
        }

        let history = await memory.recent(100)
        #expect(history.count == 40)
        #expect(stride(from: 0, to: history.count, by: 2).allSatisfy { history[$0].role == .user && history[$0 + 1].role == .assistant })
    }

    @Test("PromptBuilder is deterministic")
    func promptDeterminism() {
        let request = AdvisorRequest(
            question: "What changed?",
            technicalData: ["rsi": 42.0, "trend": "up"],
            fundamentalData: ["margin": 0.2, "growth": 0.1],
            economicContext: "Rates unchanged"
        )
        let history = [ConversationEntry(role: .user, content: "Hello")]
        let builder = PromptBuilder()
        #expect(builder.build(request, conversationHistory: history).user == builder.build(request, conversationHistory: history).user)
    }

    @Test("Default streaming adapter emits one complete response")
    func streamingAdapter() async throws {
        let provider = RecordingLLMProvider(id: "stream", response: "complete")
        var values: [String] = []
        for try await value in provider.generateStream(prompt: "p", systemPrompt: "s") {
            values.append(value)
        }
        #expect(values == ["complete"])
    }

    private func makeEngine(primary: any LLMProvider, fallback: any LLMProvider, memory: ConversationMemory = ConversationMemory(), logger: Logger? = nil) -> AIAdvisorEngine {
        AIAdvisorEngine(primary: primary, fallback: fallback, memory: memory, logger: logger ?? Logger(configuration: .init(minimumLevel: .error)))
    }
}
