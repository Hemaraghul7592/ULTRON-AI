import Foundation

/// Central entry point for the Alert Engine.
@MainActor
public final class AlertEngine {

    private var rules: [AlertRule] = []
    private let manager: AlertManager
    private let storage: AlertStorage
    private let logger: Logger
    private var restorationTask: Task<Void, Never>?
    private var pendingSave: Task<Void, Never>?
    private var lastSavedFingerprint: Data?
    private var hasMutatedBeforeRestore = false
    public weak var advisorEngine: AIAdvisorEngine?

    public init(manager: AlertManager = AlertManager(), storage: AlertStorage = InMemoryAlertStorage(), logger: Logger) {
        self.manager = manager
        self.storage = storage
        self.logger = logger
        restorationTask = Task { @MainActor [weak self] in await self?.loadPersistedState() }
    }

    public func restorePersistedState() async {
        if let restorationTask { await restorationTask.value; self.restorationTask = nil }
        else { await loadPersistedState() }
    }

    public func flushPersistence() async {
        await restorationTask?.value
        await pendingSave?.value
    }

    // MARK: - Rules

    public func addRule(_ rule: AlertRule) { rules.append(rule); scheduleSaveIfChanged() }
    public func removeRule(id: String) { let oldCount = rules.count; rules.removeAll { $0.id == id }; if oldCount != rules.count { scheduleSaveIfChanged() } }
    public func updateRule(_ rule: AlertRule) {
        guard let idx = rules.firstIndex(where: { $0.id == rule.id }) else { return }
        rules[idx] = rule
        scheduleSaveIfChanged()
    }
    public func getRules() -> [AlertRule] { rules }
    public func setRuleEnabled(id: String, enabled: Bool) {
        if let idx = rules.firstIndex(where: { $0.id == id }), rules[idx].enabled != enabled { rules[idx].enabled = enabled; scheduleSaveIfChanged() }
    }

    public func saveRules() async { scheduleSaveIfChanged(); await pendingSave?.value }
    public func loadRules() async { await restorePersistedState() }

    // MARK: - Evaluation

    public func evaluate(
        quotes: [String: Double],
        previousQuotes: [String: Double] = [:],
        portfolioValue: Double? = nil,
        cashBalance: Double? = nil,
        holdingsCount: Int? = nil,
        rsiValues: [String: Double] = [:],
        macdValues: [String: (line: Double, signal: Double)] = [:],
        averageVolume: [String: Int64] = [:],
        currentVolume: [String: Int64] = [:]
    ) async -> [Alert] {
        var results: [Alert] = []
        for rule in rules where rule.enabled {
            let alert = AlertEvaluator.evaluate(
                rule.condition, quotes: quotes, previousQuotes: previousQuotes,
                portfolioValue: portfolioValue, cashBalance: cashBalance,
                holdingsCount: holdingsCount, rsiValues: rsiValues,
                macdValues: macdValues, averageVolume: averageVolume, currentVolume: currentVolume
            )
            guard var triggered = alert else { continue }
            triggered = Alert(category: triggered.category, severity: rule.severity, title: triggered.title, message: triggered.message, symbol: triggered.symbol, value: triggered.value, threshold: triggered.threshold)

            guard let recorded = await manager.record(triggered, cooldown: rule.cooldownSeconds, oneTime: rule.oneTime) else { continue }
            results.append(recorded)
            scheduleSaveIfChanged()
            await logger.info("Alert triggered", metadata: ["title": recorded.title, "severity": recorded.severity.rawValue])

            if recorded.severity >= .high, let advisor = advisorEngine {
                await requestAIExplanation(for: recorded, advisor: advisor)
            }
        }
        return results
    }

    /// Requests an AI explanation for an alert asynchronously. Never blocks alert generation.
    private func requestAIExplanation(for alert: Alert, advisor: AIAdvisorEngine) async {
        let context = "Alert: \(alert.title). Symbol: \(alert.symbol ?? "N/A"). Value: \(alert.value?.description ?? "N/A"). Threshold: \(alert.threshold?.description ?? "N/A"). Severity: \(alert.severity.rawValue)."
        let request = AdvisorRequest(question: "Explain this financial alert concisely: \(context)")
        let response = await advisor.ask(request)
        if !response.summary.isEmpty && response.provider != "none" {
            await logger.info("AI explanation generated", metadata: ["alert": alert.title])
        }
    }

    // MARK: - History

    public func getActive() async -> [Alert] { await manager.active() }
    public func getRecent(_ count: Int = 50) async -> [Alert] { await manager.recent(count) }
    public func acknowledge(alertID: String) async { await manager.acknowledge(alertID); scheduleSaveIfChanged() }
    public func dismiss(alertID: String) async { await manager.dismiss(alertID); scheduleSaveIfChanged() }
    public func updateAlertMetadata(alertID: String, aiExplanation: String?) async { await manager.updateMetadata(alertID, aiExplanation: aiExplanation); scheduleSaveIfChanged() }
    public func clearHistory() async { await manager.clear(); scheduleSaveIfChanged() }
    public func alertCount() async -> Int { await manager.count }

    // MARK: - Notifications

    public func notificationPayload(for alert: Alert) -> NotificationPayload {
        NotificationPayload(alert: alert)
    }

    // MARK: - Default Rules

    public func addDefaultPriceRules(symbols: [String]) {
        for sym in symbols {
            addRule(AlertRule(name: "\(sym) RSI > 70", category: .technical, severity: .medium, condition: .rsiAbove(symbol: sym, threshold: 70)))
            addRule(AlertRule(name: "\(sym) RSI < 30", category: .technical, severity: .medium, condition: .rsiBelow(symbol: sym, threshold: 30)))
        }
    }

    public func addDefaultPortfolioRules() {
        addRule(AlertRule(name: "Portfolio drawdown", category: .portfolio, severity: .high, condition: .portfolioDrawdown))
        addRule(AlertRule(name: "Cash below $1000", category: .portfolio, severity: .low, condition: .cashBelow(threshold: 1000)))
    }

    private func loadPersistedState() async {
        guard !hasMutatedBeforeRestore else {
            lastSavedFingerprint = fingerprint(rules: rules, history: await manager.recent(10_000))
            return
        }
        let loadedRules = (try? await storage.loadRules()) ?? []
        let loadedHistory = (try? await storage.loadHistory()) ?? []
        rules = loadedRules
        await manager.restore(history: loadedHistory)
        lastSavedFingerprint = fingerprint(rules: rules, history: loadedHistory)
    }

    private func scheduleSaveIfChanged() {
        hasMutatedBeforeRestore = true
        let history = Task { await manager.recent(10_000) }
        let previous = pendingSave
        pendingSave = Task { [storage, logger] in
            await previous?.value
            let alerts = await history.value
            let currentFingerprint = fingerprint(rules: rules, history: alerts)
            guard currentFingerprint != lastSavedFingerprint else { return }
            lastSavedFingerprint = currentFingerprint
            do { try await storage.saveState(rules, history: alerts) }
            catch { await logger.error("Alert persistence failed", metadata: ["error": String(describing: error)]) }
        }
    }

    private func fingerprint(rules: [AlertRule], history: [Alert]) -> Data? {
        try? JSONEncoder().encode(AlertPersistenceEnvelope(rules: rules, history: history))
    }
}
