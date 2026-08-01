import Foundation

// MARK: - Request / Response

public struct AdvisorRequest: Sendable {
    public let question: String
    public let portfolioSnapshot: PortfolioSummary?
    public let technicalData: [String: any Sendable]
    public let fundamentalData: [String: any Sendable]
    public let news: [NewsArticle]
    public let economicContext: String

    public init(question: String, portfolioSnapshot: PortfolioSummary? = nil, technicalData: [String: any Sendable] = [:], fundamentalData: [String: any Sendable] = [:], news: [NewsArticle] = [], economicContext: String = "") {
        self.question = question; self.portfolioSnapshot = portfolioSnapshot
        self.technicalData = technicalData; self.fundamentalData = fundamentalData
        self.news = news; self.economicContext = economicContext
    }
}

public struct AdvisorResponse: Sendable {
    public let summary: String; public let analysis: String; public let risks: [String]; public let opportunities: [String]
    public let supportingData: String; public let confidence: Double; public let suggestedActions: [String]
    public let provider: String; public let timestamp: Date

    public init(summary: String = "", analysis: String = "", risks: [String] = [], opportunities: [String] = [], supportingData: String = "", confidence: Double = 0, suggestedActions: [String] = [], provider: String = "", timestamp: Date = Date()) {
        self.summary = summary; self.analysis = analysis; self.risks = risks; self.opportunities = opportunities
        self.supportingData = supportingData; self.confidence = confidence; self.suggestedActions = suggestedActions
        self.provider = provider; self.timestamp = timestamp
    }
}

// MARK: - Conversation Entry

public struct ConversationEntry: Sendable, Codable, Identifiable {
    public let id: String; public let role: Role; public let content: String; public let timestamp: Date
    public let referencedSymbols: [String]; public let referencedPortfolio: String?

    public enum Role: String, Sendable, Codable { case user, assistant }

    public init(id: String = UUID().uuidString, role: Role, content: String, timestamp: Date = Date(), referencedSymbols: [String] = [], referencedPortfolio: String? = nil) {
        self.id = id; self.role = role; self.content = content; self.timestamp = timestamp
        self.referencedSymbols = referencedSymbols; self.referencedPortfolio = referencedPortfolio
    }
}

// MARK: - Recommendation

public struct Recommendation: Sendable, Codable, Identifiable {
    public let id: String; public let type: RecommendationType; public let title: String; public let detail: String
    public let confidence: Double; public let source: String; public let timestamp: Date

    public init(id: String = UUID().uuidString, type: RecommendationType, title: String, detail: String = "", confidence: Double = 0, source: String = "analysis", timestamp: Date = Date()) {
        self.id = id; self.type = type; self.title = title; self.detail = detail
        self.confidence = confidence; self.source = source; self.timestamp = timestamp
    }
}

public enum RecommendationType: String, Sendable, Codable, CaseIterable {
    case risk, diversification, allocation, technical, fundamental, observation, warning
}
