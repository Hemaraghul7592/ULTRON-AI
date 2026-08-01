import Foundation

/// Builds context-rich prompts for the LLM from portfolio and market data.
public struct PromptBuilder: Sendable {

    public let systemTemplate: String

    public init(systemTemplate: String? = nil) {
        self.systemTemplate = systemTemplate ?? Self.defaultSystemPrompt
    }

    public static let defaultSystemPrompt = """
    You are ULTRON's AI Financial Advisor. You provide data-driven analysis.
    Never guess — if data is unavailable, state it. Always distinguish facts from opinions.
    """

    /// Builds a full prompt from an advisor request.
    public func build(_ request: AdvisorRequest, conversationHistory: [ConversationEntry] = []) -> (system: String, user: String) {
        var context = ""

        if let p = request.portfolioSnapshot {
            context += """
            PORTFOLIO:
            Total Value: $\(String(format: "%.2f", p.totalValue))
            Total Return: \(String(format: "%.1f", p.totalReturnPercent))%
            Cash: $\(String(format: "%.2f", p.cashBalance))
            Holdings: \(p.holdingsCount)
            """
        }

        if !request.news.isEmpty {
            context += "\nLATEST NEWS:\n"
            for n in request.news.prefix(3) { context += "- \(n.title) (\(n.source))\n" }
        }

        if !request.economicContext.isEmpty { context += "\nECONOMIC CONTEXT:\n\(request.economicContext)\n" }

        var historyText = ""
        for entry in conversationHistory.suffix(4) {
            historyText += "\(entry.role == .user ? "User" : "ULTRON"): \(entry.content)\n"
        }

        let userPrompt = """
        \(context)
        \(historyText)
        QUESTION: \(request.question)

        Provide: Summary, Analysis, Risks, Opportunities, Suggested Actions.
        """

        return (systemTemplate, userPrompt)
    }
}
