import Foundation

/// Maintains conversation history for context-aware responses.
public actor ConversationMemory {
    public struct Turn: Sendable {
        public let userEntryID: String
        public let assistantEntryID: String

        public init(userEntryID: String, assistantEntryID: String) {
            self.userEntryID = userEntryID
            self.assistantEntryID = assistantEntryID
        }
    }

    public static let pendingAssistantMessage = "ULTRON is preparing a response."

    private var entries: [ConversationEntry] = []
    private let maxEntries: Int

    public init(maxEntries: Int = 50) { self.maxEntries = maxEntries }

    public func add(role: ConversationEntry.Role, content: String, symbols: [String] = [], portfolioID: String? = nil) {
        entries.append(ConversationEntry(role: role, content: content, referencedSymbols: symbols, referencedPortfolio: portfolioID))
        if entries.count > maxEntries { entries.removeFirst(entries.count - maxEntries) }
    }

    public func beginTurn(question: String) -> Turn {
        let user = ConversationEntry(role: .user, content: question)
        let assistant = ConversationEntry(role: .assistant, content: Self.pendingAssistantMessage)
        entries.append(user)
        entries.append(assistant)
        trimToLimit()
        return Turn(userEntryID: user.id, assistantEntryID: assistant.id)
    }

    public func update(id: String, content: String) {
        guard let index = entries.firstIndex(where: { $0.id == id }) else { return }
        let entry = entries[index]
        entries[index] = ConversationEntry(id: entry.id, role: entry.role, content: content, timestamp: entry.timestamp, referencedSymbols: entry.referencedSymbols, referencedPortfolio: entry.referencedPortfolio)
    }

    public func recent(_ count: Int = 10) -> [ConversationEntry] { Array(entries.suffix(count)) }
    public func clear() { entries.removeAll() }
    public var count: Int { entries.count }

    private func trimToLimit() {
        if entries.count > maxEntries { entries.removeFirst(entries.count - maxEntries) }
    }
}

/// Generates structured recommendations from portfolio analysis.
public enum RecommendationEngine {

    public static func analyze(portfolio: PortfolioSummary) -> [Recommendation] {
        var recs: [Recommendation] = []

        if portfolio.holdingsCount <= 2 {
            recs.append(Recommendation(type: .diversification, title: "Low diversification", detail: "Your portfolio has only \(portfolio.holdingsCount) holdings. Consider diversifying.", confidence: 0.9))
        }

        if portfolio.cashBalance > portfolio.totalValue * 0.5 {
            recs.append(Recommendation(type: .allocation, title: "High cash allocation", detail: "Over 50% of your portfolio is in cash. Consider deploying capital.", confidence: 0.8))
        }

        if portfolio.totalReturnPercent < -10 {
            recs.append(Recommendation(type: .warning, title: "Significant drawdown", detail: "Your portfolio is down \(String(format: "%.1f", abs(portfolio.totalReturnPercent)))%. Review your positions.", confidence: 0.7))
        }

        return recs
    }
}
