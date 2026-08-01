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
        let history = await memory.recent(10)

        var provider: any LLMProvider
        if await primaryProvider.isAvailable { provider = primaryProvider }
        else if await fallbackProvider.isAvailable { provider = fallbackProvider }
        else { return fallbackResponse(history: history) }

        let (systemPrompt, userPrompt) = promptBuilder.build(request, conversationHistory: history)

        do {
            let raw = try await provider.generate(prompt: userPrompt, systemPrompt: systemPrompt)
            let response = parseResponse(raw, provider: provider.providerName)
            await memory.add(role: .user, content: request.question)
            await memory.add(role: .assistant, content: response.summary)
            return response
        } catch {
            await logger.warning("LLM generation failed, using fallback", metadata: ["error": String(describing: error)])
            return fallbackResponse(history: history)
        }
    }

    /// Generates recommendations based on portfolio data.
    public func recommend(portfolio: PortfolioSummary) -> [Recommendation] {
        RecommendationEngine.analyze(portfolio: portfolio)
    }

    /// Returns conversation history.
    public func getHistory() async -> [ConversationEntry] { await memory.recent() }

    /// Clears conversation history.
    public func clearHistory() async { await memory.clear() }

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

    private func fallbackResponse(history: [ConversationEntry]) -> AdvisorResponse {
        AdvisorResponse(
            summary: "I'm currently unable to access my AI providers. Please try again shortly.",
            risks: [], opportunities: [],
            confidence: 0, provider: "none"
        )
    }
}
