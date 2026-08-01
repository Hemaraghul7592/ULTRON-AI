import Foundation
import Testing

@testable import ULTRON

// MARK: - Mock Provider

private actor MockProvider: ServiceProvider {
    let providerID: String
    let providerName: String
    let category: ServiceCategory
    let capabilities: Set<ServiceCapability>

    var initCalled = false
    var shutdownCalled = false
    var resetCalled = false
    private var executeValue: Result<any Sendable, any Error> = .success("default")
    private var statusValue: HealthStatus = .healthy
    var executeCount = 0

    init(id: String, name: String = "", category: ServiceCategory = .ai, capabilities: Set<ServiceCapability> = [.chat]) {
        providerID = id
        providerName = name.isEmpty ? id : name
        self.category = category
        self.capabilities = capabilities
    }

    func setResult(_ result: Result<any Sendable, any Error>) { executeValue = result }
    func setHealth(_ status: HealthStatus) { statusValue = status }

    func initialize() async throws { initCalled = true }
    func healthCheck() async -> HealthStatus { statusValue }
    func execute(request: any Sendable) async throws -> any Sendable {
        executeCount += 1
        switch executeValue {
        case .success(let v): return v
        case .failure(let e): throw e
        }
    }
    func shutdown() async { shutdownCalled = true }
    func reset() async { resetCalled = true }
}

// MARK: - Retry Tests

@Suite struct RetryPolicyTests {
    @Test("Defaults") func testDefaults() {
        let p = RetryPolicy.standard
        #expect(p.maxAttempts == 3)
    }
    @Test("NoRetry") func testNoRetry() {
        #expect(RetryPolicy.noRetry.maxAttempts == 1)
    }
    @Test("Delay increases") func testDelayIncreases() {
        let p = RetryPolicy.standard
        #expect(p.delay(forAttempt: 1) >= p.delay(forAttempt: 0))
    }
}

@Suite struct RetryEngineTests {
    @Test("First attempt success") func testSuccess() async throws {
        let r = try await RetryEngine().execute(with: .noRetry) { "ok" }
        #expect(r == "ok")
    }
    @Test("Retries then succeeds") func testRetrySuccess() async throws {
        final class Counter { var value = 0 }
        let c = Counter()
        let r = try await RetryEngine().execute(with: .standard) {
            c.value += 1; if c.value < 3 { throw NSError(domain: "t", code: 1) }; return "ok"
        }
        #expect(r == "ok")
        #expect(c.value == 3)
    }
    @Test("Exhausted throws") func testExhausted() async {
        final class Counter { var value = 0 }
        let c = Counter()
        do {
            _ = try await RetryEngine().execute(with: .fast) { () -> String in c.value += 1; throw NSError(domain: "t", code: 1) }
        } catch { #expect(c.value == 2) }
    }
}

// MARK: - Circuit Breaker

@Suite struct CircuitBreakerTests {
    @Test("Starts closed") func testStartsClosed() async {
        #expect(await CircuitBreaker().allowRequest() == true)
    }
    @Test("Opens after threshold") func testOpens() async {
        let cb = CircuitBreaker(failureThreshold: 3, cooldownDuration: 999)
        for _ in 0..<3 { await cb.recordFailure() }
        #expect(await cb.allowRequest() == false)
    }
    @Test("Reset clears") func testReset() async {
        let cb = CircuitBreaker(failureThreshold: 1)
        await cb.recordFailure()
        await cb.reset()
        #expect(await cb.allowRequest() == true)
    }
    @Test("Half-open to closed on success") func testHalfOpen() async {
        let cb = CircuitBreaker(failureThreshold: 1, cooldownDuration: 0, recoverySuccesses: 1)
        await cb.recordFailure()
        _ = await cb.allowRequest()
        await cb.recordSuccess()
        #expect(await cb.allowRequest() == true)
    }
}

// MARK: - Orchestrator Tests

@MainActor
@Suite struct ServiceOrchestratorTests {

    @Test("Register and retrieve provider IDs") func testRegistration() async throws {
        let o = makeOrchestrator()
        o.register(MockProvider(id: "p1"), configuration: ProviderConfig(providerID: "p1"))
        try await o.initializeAll()
        #expect(o.registeredProviderIDs() == ["p1"])
    }

    @Test("Priority ordering") func testPriorityOrdering() {
        let o = makeOrchestrator()
        o.register(MockProvider(id: "low"), configuration: ProviderConfig(providerID: "low", priority: 10))
        o.register(MockProvider(id: "high"), configuration: ProviderConfig(providerID: "high", priority: 0))
        o.register(MockProvider(id: "mid"), configuration: ProviderConfig(providerID: "mid", priority: 5))
        #expect(o.registeredProviderIDs() == ["high", "mid", "low"])
    }

    @Test("Execute succeeds") func testExecuteSuccess() async throws {
        let o = makeOrchestrator()
        o.register(MockProvider(id: "p1"), configuration: ProviderConfig(providerID: "p1"))
        try await o.initializeAll()
        let result = try await o.execute(request: "hello")
        #expect(result as? String == "default")
    }

    @Test("Failover to next provider") func testFailover() async throws {
        let o = makeOrchestrator()
        let fail = MockProvider(id: "fail")
        await fail.setResult(.failure(NSError(domain: "t", code: 1)))
        let ok = MockProvider(id: "ok")
        await ok.setResult(.success("recovered"))

        o.register(fail, configuration: ProviderConfig(providerID: "fail", priority: 0, retryPolicy: .noRetry))
        o.register(ok, configuration: ProviderConfig(providerID: "ok", priority: 1))
        try await o.initializeAll()

        let result = try await o.execute(request: "req")
        #expect(result as? String == "recovered")
    }

    @Test("All exhausted throws") func testAllExhausted() async {
        let o = makeOrchestrator()
        let p1 = MockProvider(id: "p1")
        await p1.setResult(.failure(NSError(domain: "t", code: 1)))
        o.register(p1, configuration: ProviderConfig(providerID: "p1", retryPolicy: .noRetry))

        do {
            _ = try await o.execute(request: "req")
            Issue.record("Expected throw")
        } catch let e as OrchestrationError {
            if case .allProvidersExhausted = e {} else { Issue.record("Wrong error: \(e)") }
        } catch { Issue.record("Unexpected: \(error)") }
    }

    @Test("Capability filtering") func testCapabilityFiltering() async throws {
        let o = makeOrchestrator()
        o.register(MockProvider(id: "no"), configuration: ProviderConfig(providerID: "no", priority: 0, capabilities: []))
        o.register(MockProvider(id: "yes", capabilities: [.chat]), configuration: ProviderConfig(providerID: "yes", priority: 1, capabilities: [.chat]))
        try await o.initializeAll()
        let r = try await o.execute(request: "test", capability: .chat)
        #expect(r as? String == "default")
    }

    @Test("Disabled provider skipped") func testDisabled() async throws {
        let o = makeOrchestrator()
        let disabled = MockProvider(id: "d")
        await disabled.setResult(.failure(NSError(domain: "t", code: 1)))
        let enabled = MockProvider(id: "e")
        await enabled.setResult(.success("works"))

        o.register(disabled, configuration: ProviderConfig(providerID: "d", priority: 0, retryPolicy: .noRetry, enabled: false))
        o.register(enabled, configuration: ProviderConfig(providerID: "e", priority: 1))
        try await o.initializeAll()

        let r = try await o.execute(request: "req")
        #expect(r as? String == "works")
    }

    @Test("Health reports") func testHealth() async throws {
        let o = makeOrchestrator()
        o.register(MockProvider(id: "p1"), configuration: ProviderConfig(providerID: "p1"))
        try await o.initializeAll()
        #expect(o.providerHealth()[0].status == .healthy)
    }

    @Test("Shutdown all") func testShutdown() async {
        let o = makeOrchestrator()
        let p1 = MockProvider(id: "p1")
        let p2 = MockProvider(id: "p2")
        o.register(p1, configuration: ProviderConfig(providerID: "p1"))
        o.register(p2, configuration: ProviderConfig(providerID: "p2"))
        await o.shutdownAll()
        #expect(await p1.shutdownCalled == true)
        #expect(await p2.shutdownCalled == true)
    }

    @Test("Reset all clears metrics") func testResetAll() async throws {
        let o = makeOrchestrator()
        let p1 = MockProvider(id: "p1")
        await p1.setResult(.failure(NSError(domain: "t", code: 1)))
        o.register(p1, configuration: ProviderConfig(providerID: "p1", retryPolicy: .noRetry))
        _ = try? await o.execute(request: "req")
        await o.resetAll()
        #expect(o.providerHealth()[0].metrics.totalRequests == 0)
    }

    private func makeOrchestrator() -> ServiceOrchestrator<MockProvider> {
        ServiceOrchestrator(
            config: OrchestratorConfig(category: .ai),
            logger: Logger(configuration: .init(minimumLevel: .error))
        )
    }
}

// MARK: - Error Tests

@Suite struct OrchestrationErrorTests {
    @Test("User message hides provider names") func testMessages() {
        let e = OrchestrationError.allProvidersExhausted(category: .ai, attempted: ["p1", "p2"])
        #expect(e.description.contains("ai"))
        #expect(!e.description.contains("p1"))
    }
}
