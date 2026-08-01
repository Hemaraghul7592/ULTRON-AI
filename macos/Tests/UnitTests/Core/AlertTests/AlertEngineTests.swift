import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite struct AlertEngineTests {

    // MARK: - Evaluator

    @Test("Price above triggers alert") func testPriceAbove() {
        let alert = AlertEvaluator.evaluate(.priceAbove(symbol: "AAPL", threshold: 150), quotes: ["AAPL": 160])
        #expect(alert != nil)
        #expect(alert?.category == .price)
    }

    @Test("Price above not triggered below threshold") func testPriceAboveNotTriggered() {
        #expect(AlertEvaluator.evaluate(.priceAbove(symbol: "AAPL", threshold: 150), quotes: ["AAPL": 140]) == nil)
    }

    @Test("Price below triggers alert") func testPriceBelow() {
        let alert = AlertEvaluator.evaluate(.priceBelow(symbol: "AAPL", threshold: 100), quotes: ["AAPL": 90])
        #expect(alert != nil)
    }

    @Test("RSI above triggers alert") func testRSIAbove() {
        let alert = AlertEvaluator.evaluate(.rsiAbove(symbol: "AAPL", threshold: 70), quotes: [:], rsiValues: ["AAPL": 75])
        #expect(alert != nil)
        #expect(alert?.category == .technical)
    }

    @Test("RSI below triggers alert") func testRSIBelow() {
        let alert = AlertEvaluator.evaluate(.rsiBelow(symbol: "AAPL", threshold: 30), quotes: [:], rsiValues: ["AAPL": 25])
        #expect(alert != nil)
    }

    @Test("Portfolio value above triggers") func testPortfolioAbove() {
        let alert = AlertEvaluator.evaluate(.portfolioValueAbove(threshold: 50000), quotes: [:], portfolioValue: 60000)
        #expect(alert != nil)
    }

    @Test("Portfolio drawdown triggers") func testDrawdown() {
        let alert = AlertEvaluator.evaluate(.portfolioDrawdown, quotes: [:], portfolioValue: -5000)
        #expect(alert != nil)
    }

    @Test("Cash below triggers") func testCashBelow() {
        let alert = AlertEvaluator.evaluate(.cashBelow(threshold: 1000), quotes: [:], cashBalance: 500)
        #expect(alert != nil)
    }

    @Test("OR condition triggers on first match") func testOrCondition() {
        let alert = AlertEvaluator.evaluate(.or(.priceAbove(symbol: "AAPL", threshold: 150), .priceAbove(symbol: "GOOGL", threshold: 500)), quotes: ["AAPL": 160])
        #expect(alert != nil)
    }

    @Test("OR condition triggers on second match") func testOrConditionSecond() {
        let alert = AlertEvaluator.evaluate(.or(.priceAbove(symbol: "AAPL", threshold: 500), .priceAbove(symbol: "GOOGL", threshold: 100)), quotes: ["GOOGL": 120])
        #expect(alert != nil)
    }

    @Test("NOT condition does not trigger") func testNotCondition() {
        #expect(AlertEvaluator.evaluate(.not(.alwaysTrue), quotes: [:]) == nil)
    }

    // MARK: - Alert Manager

    @Test("Alert manager records and deduplicates") func testManagerDedup() async {
        let manager = AlertManager(maxHistory: 100)
        let alert = Alert(category: .price, title: "Test")
        let r1 = await manager.record(alert, cooldown: 60)
        #expect(r1 != nil)
        let r2 = await manager.record(alert, cooldown: 60)
        #expect(r2 == nil)
    }

    @Test("Alert manager one-time rules") func testManagerOneTime() async {
        let manager = AlertManager(maxHistory: 100)
        let alert = Alert(category: .price, title: "OneTime")
        _ = await manager.record(alert, oneTime: true)
        #expect(await manager.record(alert, oneTime: true) == nil)
    }

    @Test("Alert manager active excludes dismissed") func testManagerActive() async {
        let manager = AlertManager(maxHistory: 100)
        let a = Alert(category: .price, title: "Test")
        _ = await manager.record(a)
        await manager.dismiss(a.id)
        #expect(await manager.active().isEmpty)
    }

    @Test("Alert manager acknowledge") func testManagerAcknowledge() async {
        let manager = AlertManager(maxHistory: 100)
        let a = Alert(category: .price, title: "Test")
        _ = await manager.record(a)
        await manager.acknowledge(a.id)
        let recent = await manager.recent()
        #expect(recent.first?.acknowledgedAt != nil)
    }

    // MARK: - Alert Engine

    @Test("Alert engine evaluates rules and returns alerts") func testEngineEvaluate() async {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        engine.addRule(AlertRule(name: "AAPL > 150", category: .price, condition: .priceAbove(symbol: "AAPL", threshold: 150)))
        engine.addRule(AlertRule(name: "RSI > 70", category: .technical, condition: .rsiAbove(symbol: "AAPL", threshold: 70)))
        let results = await engine.evaluate(quotes: ["AAPL": 160], portfolioValue: nil, rsiValues: ["AAPL": 75])
        #expect(results.count == 2)
    }

    @Test("Alert engine respects disabled rules") func testEngineDisabled() async {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        var rule = AlertRule(name: "Test", category: .price, condition: .priceAbove(symbol: "AAPL", threshold: 150))
        rule.enabled = false
        engine.addRule(rule)
        let results = await engine.evaluate(quotes: ["AAPL": 160])
        #expect(results.isEmpty)
    }

    @Test("Alert engine empty evaluation") func testEngineEmpty() async {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let results = await engine.evaluate(quotes: [:])
        #expect(results.isEmpty)
    }

    @Test("Default price rules added") func testDefaultPriceRules() {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        engine.addDefaultPriceRules(symbols: ["AAPL"])
        #expect(engine.getRules().count == 2)
    }

    @Test("Default portfolio rules added") func testDefaultPortfolioRules() {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        engine.addDefaultPortfolioRules()
        #expect(engine.getRules().count == 2)
    }

    @Test("Notification payload from alert") func testNotificationPayload() {
        let alert = Alert(category: .price, severity: .high, title: "Test", message: "Msg", symbol: "AAPL")
        let payload = NotificationPayload(alert: alert)
        #expect(payload.category == .price)
        #expect(payload.severity == .high)
        #expect(payload.symbol == "AAPL")
    }

    @Test("Alert engine acknowledge and dismiss") func testEngineAckDismiss() async {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        engine.addRule(AlertRule(name: "T", category: .price, condition: .alwaysTrue))
        let results = await engine.evaluate(quotes: [:])
        #expect(results.count == 1)
        let id = results[0].id
        await engine.acknowledge(alertID: id)
        await engine.dismiss(alertID: id)
        #expect(await engine.getActive().isEmpty)
    }

    @Test("Alert engine clear history") func testEngineClear() async {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        engine.addRule(AlertRule(name: "T", category: .price, condition: .alwaysTrue))
        _ = await engine.evaluate(quotes: [:])
        await engine.clearHistory()
        #expect(await engine.alertCount() == 0)
    }

    // MARK: - Completed Conditions

    @Test("Percent gain triggers with previous quote") func testPercentGain() {
        let alert = AlertEvaluator.evaluate(.percentGain(symbol: "AAPL", percent: 5), quotes: ["AAPL": 110], previousQuotes: ["AAPL": 100])
        #expect(alert != nil)
        #expect(alert?.category == .price)
    }

    @Test("Percent gain not triggered below threshold") func testPercentGainNotTriggered() {
        #expect(AlertEvaluator.evaluate(.percentGain(symbol: "AAPL", percent: 5), quotes: ["AAPL": 103], previousQuotes: ["AAPL": 100]) == nil)
    }

    @Test("Percent loss triggers with previous quote") func testPercentLoss() {
        let alert = AlertEvaluator.evaluate(.percentLoss(symbol: "AAPL", percent: 5), quotes: ["AAPL": 90], previousQuotes: ["AAPL": 100])
        #expect(alert != nil)
        #expect(alert?.severity == .high)
    }

    @Test("MACD bullish crossover triggers") func testMACDBullish() {
        let alert = AlertEvaluator.evaluate(.macdCrossover(symbol: "AAPL"), quotes: [:], macdValues: ["AAPL": (line: 2.0, signal: 1.0)])
        #expect(alert != nil)
        #expect(alert?.title.contains("bullish") == true)
    }

    @Test("MACD bearish crossover triggers") func testMACDBearish() {
        let alert = AlertEvaluator.evaluate(.macdCrossover(symbol: "AAPL"), quotes: [:], macdValues: ["AAPL": (line: -2.0, signal: -1.0)])
        #expect(alert != nil)
        #expect(alert?.title.contains("bearish") == true)
    }

    @Test("MACD no crossover returns nil") func testMACDNone() {
        #expect(AlertEvaluator.evaluate(.macdCrossover(symbol: "AAPL"), quotes: [:], macdValues: ["AAPL": (line: 1.0, signal: 1.0)]) == nil)
    }

    @Test("Volume spike triggers") func testVolumeSpike() {
        let alert = AlertEvaluator.evaluate(.volumeSpike(symbol: "AAPL", multiplier: 2), quotes: [:], averageVolume: ["AAPL": 1_000_000], currentVolume: ["AAPL": 3_000_000])
        #expect(alert != nil)
    }

    @Test("Volume spike not triggered below multiplier") func testVolumeSpikeNotTriggered() {
        #expect(AlertEvaluator.evaluate(.volumeSpike(symbol: "AAPL", multiplier: 2), quotes: [:], averageVolume: ["AAPL": 1_000_000], currentVolume: ["AAPL": 1_500_000]) == nil)
    }

    @Test("NOT condition inverts evaluation") func testNotInvert() {
        let alert = AlertEvaluator.evaluate(.not(.priceAbove(symbol: "AAPL", threshold: 200)), quotes: ["AAPL": 150])
        #expect(alert != nil)
    }

    @Test("NOT condition returns nil when inner triggers") func testNotInnerTriggers() {
        #expect(AlertEvaluator.evaluate(.not(.priceAbove(symbol: "AAPL", threshold: 100)), quotes: ["AAPL": 150]) == nil)
    }

    @Test("Nested AND/OR/NOT works correctly") func testNestedLogic() {
        let condition: AlertCondition = .and(.not(.priceBelow(symbol: "AAPL", threshold: 100)), .or(.rsiAbove(symbol: "AAPL", threshold: 70), .rsiAbove(symbol: "GOOGL", threshold: 70)))
        #expect(AlertEvaluator.evaluate(condition, quotes: ["AAPL": 150, "GOOGL": 140], rsiValues: ["GOOGL": 75]) != nil)
        #expect(AlertEvaluator.evaluate(condition, quotes: ["AAPL": 80], rsiValues: [:]) == nil)
    }

    @Test("AND condition both must trigger") func testAndBoth() {
        let condition: AlertCondition = .and(.rsiAbove(symbol: "AAPL", threshold: 70), .priceAbove(symbol: "AAPL", threshold: 100))
        #expect(AlertEvaluator.evaluate(condition, quotes: ["AAPL": 50], rsiValues: ["AAPL": 75]) == nil)
        #expect(AlertEvaluator.evaluate(condition, quotes: ["AAPL": 150], rsiValues: ["AAPL": 75]) != nil)
    }

    // MARK: - Storage

    @Test("Alert storage saves and loads rules") func testStorage() async throws {
        let engine = AlertEngine(storage: InMemoryAlertStorage(), logger: Logger(configuration: .init(minimumLevel: .error)))
        engine.addRule(AlertRule(name: "Test", category: .price, condition: .alwaysTrue))
        await engine.saveRules()
        let engine2 = AlertEngine(storage: InMemoryAlertStorage(), logger: Logger(configuration: .init(minimumLevel: .error)))
        #expect(engine2.getRules().isEmpty)
        engine2.addRule(AlertRule(name: "Test", category: .price, condition: .alwaysTrue))
        await engine2.saveRules()
        await engine2.loadRules()
        #expect(engine2.getRules().count == 1)
    }

    // MARK: - Cooldown

    @Test("Cooldown prevents repeated alerts") func testCooldown() async {
        let engine = AlertEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        engine.addRule(AlertRule(name: "T", category: .price, condition: .alwaysTrue, cooldownSeconds: 3600))
        let r1 = await engine.evaluate(quotes: [:])
        #expect(r1.count == 1)
        let r2 = await engine.evaluate(quotes: [:])
        #expect(r2.isEmpty)
    }
}
