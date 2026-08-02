import Testing

@testable import ULTRON

@MainActor
@Suite(.serialized) struct LifecycleIntegrationTests {
    @Test("Concurrent startup requests execute once")
    func concurrentStartup() async throws {
        let sequence = StartupSequence()
        let hook = IntegrationHook(label: "Once", phase: .configuration)
        sequence.register(hook)
        try await withThrowingTaskGroup(of: Void.self) { group in
            for _ in 0..<4 { group.addTask { try await sequence.execute() } }
            try await group.waitForAll()
        }
        #expect(sequence.state == .completed)
        #expect(hook.startCount == 1)
    }

    @Test("Startup aggregates failures and continues safe hooks")
    func startupFailureAggregation() async {
        let sequence = StartupSequence()
        let failing = IntegrationHook(label: "Failing", phase: .configuration, shouldFail: true)
        let following = IntegrationHook(label: "Following", phase: .logging)
        sequence.register([failing, following])
        do {
            try await sequence.execute()
            Issue.record("Expected startup failure")
        } catch let error as StartupSequence.StartupError {
            if case .hookFailures(let errors) = error { #expect(errors.count == 1) }
        } catch { Issue.record("Unexpected error: \(error)") }
        #expect(failing.startCount == 1)
        #expect(following.startCount == 1)
        #expect(sequence.state == .failed)
    }

    @Test("Startup can retry after a transient failure")
    func startupRetry() async throws {
        let sequence = StartupSequence()
        let hook = IntegrationHook(label: "Retry", phase: .configuration, shouldFail: true)
        sequence.register(hook)
        do { try await sequence.execute() } catch { }
        hook.shouldFail = false
        sequence.resetAfterFailure()
        try await sequence.execute()
        #expect(hook.startCount == 2)
        #expect(sequence.state == .completed)
    }

    @Test("Composition root blocks resolution until ready")
    func compositionReadiness() async {
        let root = ApplicationCompositionRoot()
        do {
            _ = try await root.resolve(Logger.self)
            Issue.record("Expected composition root readiness failure")
        } catch let error as ApplicationCompositionRoot.Error {
            #expect(error == .notReady)
        } catch { Issue.record("Unexpected error: \(error)") }
        root.markReady()
        #expect((try? await root.resolve(Logger.self)) != nil)
    }

    @Test("Shutdown requests execute hooks once")
    func shutdownOnce() async {
        let sequence = ShutdownSequence()
        let hook = IntegrationHook(label: "Shutdown", phase: .ready)
        sequence.register(hook)
        await withTaskGroup(of: Void.self) { group in
            for _ in 0..<3 { group.addTask { await sequence.execute() } }
            await group.waitForAll()
        }
        #expect(sequence.state == .completed)
        #expect(hook.shutdownCount == 1)
    }
}

@MainActor
private final class IntegrationHook: LifecycleHook {
    let label: String
    let phase: StartupPhase
    var shouldFail: Bool
    var startCount = 0
    var shutdownCount = 0

    init(label: String, phase: StartupPhase, shouldFail: Bool = false) {
        self.label = label; self.phase = phase; self.shouldFail = shouldFail
    }

    func onStartup() async throws {
        startCount += 1
        if shouldFail { throw IntegrationError.failure }
    }

    func onShutdown() async { shutdownCount += 1 }
}

private enum IntegrationError: Error { case failure }
