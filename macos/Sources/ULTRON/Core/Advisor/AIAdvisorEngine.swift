import Foundation

/// The central AI Financial Advisor engine.
///
/// Integrates with all existing engines to provide intelligent,
/// context-aware financial analysis and recommendations.
@MainActor
public final class AIAdvisorEngine {

    private let primaryProvider: any LLMProvider
    private let fallbackProvider: any LLMProvider
    private let promptBuilder: PromptBuilder
    private let memory: ConversationMemory
    private let logger: Logger
    private var latestTurn: ConversationMemory.Turn?
    private var promptsByTurn: [String: (system: String, user: String)] = [:]

    public init(
        primary: any LLMProvider,
        fallback: any LLMProvider,
        promptBuilder: PromptBuilder = PromptBuilder(),
        memory: ConversationMemory = ConversationMemory(),
        logger: Logger
    ) {
        primaryProvider = primary
        fallbackProvider = fallback
        self.promptBuilder = promptBuilder
        self.memory = memory
        self.logger = logger
    }

    /// Processes a financial question and returns an advisor response.
    public func ask(_ request: AdvisorRequest) async -> AdvisorResponse {
        do {
            return try await askCancellable(request)
        } catch {
            return fallbackResponse()
        }
    }

    public func askCancellable(_ request: AdvisorRequest) async throws -> AdvisorResponse {
        try await perform(request, turn: nil)
    }

    public func retryCancellable(_ request: AdvisorRequest) async throws -> AdvisorResponse {
        try await perform(request, turn: nil, promptSource: latestTurn)
    }

    private func perform(_ request: AdvisorRequest, turn existingTurn: ConversationMemory.Turn?, promptSource: ConversationMemory.Turn? = nil) async throws -> AdvisorResponse {
        try Task.checkCancellation()
        let history = await memory.recent(10)
        let turn: ConversationMemory.Turn
        if let existingTurn {
            turn = existingTurn
        } else {
            turn = await memory.beginTurn(question: request.question)
        }
        latestTurn = turn
        let prompts: (system: String, user: String)
        if let sourceTurn = existingTurn ?? promptSource, let cached = promptsByTurn[sourceTurn.assistantEntryID] {
            prompts = cached
        } else {
            prompts = promptBuilder.build(request, conversationHistory: history)
            promptsByTurn[turn.assistantEntryID] = prompts
        }

        do {
            let result = try await generateWithFallback(prompt: prompts.user, systemPrompt: prompts.system)
            let response = parseResponse(result.text, provider: result.provider)
            await memory.update(id: turn.assistantEntryID, content: response.summary)
            return response
        } catch is CancellationError {
            await memory.update(id: turn.assistantEntryID, content: "The AI request was cancelled.")
            throw CancellationError()
        } catch {
            await memory.update(id: turn.assistantEntryID, content: "The AI request failed. Please try again.")
            await logger.warning("LLM generation failed", metadata: ["error": String(describing: error)])
            return fallbackResponse()
        }
    }

    private func generateWithFallback(prompt: String, systemPrompt: String) async throws -> (text: String, provider: String) {
        var primaryAttempted = false
        if await primaryProvider.isAvailable {
            primaryAttempted = true
            do {
                return (try await primaryProvider.generate(prompt: prompt, systemPrompt: systemPrompt), primaryProvider.providerName)
            } catch is CancellationError {
                throw CancellationError()
            } catch {
                await logger.warning("Primary LLM failed, trying fallback", metadata: ["error": String(describing: error)])
            }
        }

        if (!primaryAttempted || primaryProvider.providerID != fallbackProvider.providerID), await fallbackProvider.isAvailable {
            return (try await fallbackProvider.generate(prompt: prompt, systemPrompt: systemPrompt), fallbackProvider.providerName)
        }
        throw LLMError.unavailable("No AI provider is available")
    }

    /// Generates recommendations based on portfolio data.
    public func recommend(portfolio: PortfolioSummary) -> [Recommendation] {
        RecommendationEngine.analyze(portfolio: portfolio)
    }

    /// Returns conversation history.
    public func getHistory() async -> [ConversationEntry] { await memory.recent() }

    /// Clears conversation history.
    public func clearHistory() async {
        await memory.clear()
        latestTurn = nil
        promptsByTurn.removeAll()
    }

    /// Health check for all providers.
    public func healthCheck() async -> (primary: Bool, fallback: Bool) {
        (await primaryProvider.healthCheck(), await fallbackProvider.healthCheck())
    }

    // MARK: - Helpers

    private func parseResponse(_ raw: String, provider: String) -> AdvisorResponse {
        let sections = raw.components(separatedBy: "\n\n")
        var summary = "", analysis = "", risks: [String] = [], opportunities: [String] = [], actions: [String] = []

        for section in sections {
            let lower = section.lowercased()
            if lower.contains("summary") || summary.isEmpty { summary = section }
            if lower.contains("analysis") { analysis = section }
            if lower.contains("risk") { risks = section.components(separatedBy: "\n").filter { $0.hasPrefix("-") || $0.hasPrefix("*") } }
            if lower.contains("opportunit") { opportunities = section.components(separatedBy: "\n").filter { $0.hasPrefix("-") || $0.hasPrefix("*") } }
            if lower.contains("action") || lower.contains("suggest") { actions = section.components(separatedBy: "\n").filter { $0.hasPrefix("-") || $0.hasPrefix("*") } }
        }

        return AdvisorResponse(summary: summary, analysis: analysis, risks: risks, opportunities: opportunities, supportingData: "", confidence: 0.7, suggestedActions: actions, provider: provider)
    }

    private func fallbackResponse() -> AdvisorResponse {
        AdvisorResponse(
            summary: "I'm currently unable to access my AI providers. Please try again shortly.",
            risks: [], opportunities: [],
            confidence: 0, provider: "none"
        )
    }
}
