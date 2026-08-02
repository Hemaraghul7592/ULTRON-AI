import Foundation

/// Manages alert storage, history, deduplication, and cooldowns.
public actor AlertManager {
    private var history: [Alert] = []
    private var lastTriggered: [String: Date] = [:]
    private var oneTimeTriggered: Set<String> = []
    private let maxHistory: Int

    public init(maxHistory: Int = 1000) { self.maxHistory = maxHistory }

    /// Records an alert. Returns nil if suppressed by cooldown or one-time rule.
    public func record(_ alert: Alert, cooldown: TimeInterval = 0, oneTime: Bool = false) -> Alert? {
        let key = alertKey(alert)

        if oneTime && oneTimeTriggered.contains(key) { return nil }
        if let last = lastTriggered[key], Date().timeIntervalSince(last) < cooldown { return nil }

        lastTriggered[key] = Date()
        if oneTime { oneTimeTriggered.insert(key) }
        history.append(alert)
        if history.count > maxHistory { history.removeFirst(history.count - maxHistory) }
        return alert
    }

    public func acknowledge(_ id: String) {
        if let idx = history.firstIndex(where: { $0.id == id }) { history[idx].acknowledgedAt = Date() }
    }

    public func dismiss(_ id: String) {
        if let idx = history.firstIndex(where: { $0.id == id }) { history[idx].dismissedAt = Date() }
    }

    public func updateMetadata(_ id: String, aiExplanation: String?) {
        if let idx = history.firstIndex(where: { $0.id == id }) { history[idx].aiExplanation = aiExplanation }
    }

    public func recent(_ count: Int = 50) -> [Alert] { Array(history.suffix(count)).reversed() }
    public func active() -> [Alert] { history.filter { $0.dismissedAt == nil } }
    public func clear() { history.removeAll(); lastTriggered.removeAll(); oneTimeTriggered.removeAll() }
    public var count: Int { history.count }

    public func restore(history: [Alert]) {
        self.history = Array(history.suffix(maxHistory))
        lastTriggered = Dictionary(uniqueKeysWithValues: self.history.map { (alertKey($0), $0.triggeredAt) })
        oneTimeTriggered.removeAll()
    }

    private func alertKey(_ alert: Alert) -> String { "\(alert.category.rawValue):\(alert.symbol ?? ""):\(alert.title)" }
}
