import Foundation

// MARK: - Alert

public struct Alert: Sendable, Codable, Identifiable {
    public let id: String
    public let category: AlertCategory
    public let severity: AlertSeverity
    public let title: String
    public let message: String
    public let symbol: String?
    public let value: Double?
    public let threshold: Double?
    public let triggeredAt: Date
    public var acknowledgedAt: Date?
    public var dismissedAt: Date?
    public var aiExplanation: String?

    public init(id: String = UUID().uuidString, category: AlertCategory, severity: AlertSeverity = .info, title: String, message: String = "", symbol: String? = nil, value: Double? = nil, threshold: Double? = nil, triggeredAt: Date = Date(), aiExplanation: String? = nil) {
        self.id = id; self.category = category; self.severity = severity; self.title = title
        self.message = message; self.symbol = symbol; self.value = value; self.threshold = threshold
        self.triggeredAt = triggeredAt; self.aiExplanation = aiExplanation
    }
}

public enum AlertCategory: String, Sendable, Codable, CaseIterable {
    case price, portfolio, technical, fundamental, news, economic, system
}

public enum AlertSeverity: String, Sendable, Codable, CaseIterable, Comparable {
    case info, low, medium, high, critical
    private var order: Int { switch self { case .info: 0; case .low: 1; case .medium: 2; case .high: 3; case .critical: 4 } }
    public static func < (lhs: AlertSeverity, rhs: AlertSeverity) -> Bool { lhs.order < rhs.order }
}

// MARK: - Alert Rule

public struct AlertRule: Sendable, Codable, Identifiable {
    public let id: String
    public let name: String
    public let category: AlertCategory
    public let severity: AlertSeverity
    public let condition: AlertCondition
    public var enabled: Bool
    public let cooldownSeconds: TimeInterval
    public let oneTime: Bool

    public init(id: String = UUID().uuidString, name: String, category: AlertCategory, severity: AlertSeverity = .medium, condition: AlertCondition, enabled: Bool = true, cooldownSeconds: TimeInterval = 300, oneTime: Bool = false) {
        self.id = id; self.name = name; self.category = category; self.severity = severity
        self.condition = condition; self.enabled = enabled; self.cooldownSeconds = cooldownSeconds; self.oneTime = oneTime
    }
}

// MARK: - Condition

public indirect enum AlertCondition: Sendable, Codable {
    case priceAbove(symbol: String, threshold: Double)
    case priceBelow(symbol: String, threshold: Double)
    case percentGain(symbol: String, percent: Double)
    case percentLoss(symbol: String, percent: Double)
    case rsiAbove(symbol: String, threshold: Double)
    case rsiBelow(symbol: String, threshold: Double)
    case macdCrossover(symbol: String)
    case portfolioValueAbove(threshold: Double)
    case portfolioValueBelow(threshold: Double)
    case portfolioDrawdown
    case cashBelow(threshold: Double)
    case holdingConcentration(percent: Double)
    case volumeSpike(symbol: String, multiplier: Double)
    case and(AlertCondition, AlertCondition)
    case or(AlertCondition, AlertCondition)
    case not(AlertCondition)
    case alwaysTrue
}

// MARK: - Notification Payload

public struct NotificationPayload: Sendable, Codable {
    public let alertID: String
    public let title: String
    public let body: String
    public let category: AlertCategory
    public let severity: AlertSeverity
    public let symbol: String?
    public let timestamp: Date

    public init(alert: Alert) {
        alertID = alert.id; title = alert.title; body = alert.message; category = alert.category
        severity = alert.severity; symbol = alert.symbol; timestamp = alert.triggeredAt
    }
}
