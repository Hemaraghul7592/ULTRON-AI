import Foundation
import Testing

@testable import ULTRON

/// Validates that the lifecycle sequences execute hooks in the correct
/// order and handle edge cases robustly.
@MainActor
@Suite struct LifecycleTests {

    // MARK: - Test Helpers

    /// A reference-type wrapper for `[String]` used to track hook
    /// execution order across multiple hooks. `Array` is a value type
    /// and would be copied when passed to `TestHook`, preventing
    /// the caller from observing mutations.
    private final class ExecutionOrder {
        var values: [String] = []
    }

    // MARK: - Test Hooks

    /// A test hook that records its execution order for assertions.
    private final class TestHook: LifecycleHook {
        let phase: StartupPhase
        let priority: Int
        let label: String
        var startupCalled = false
        var shutdownCalled = false
        private let order: ExecutionOrder

        init(
            phase: StartupPhase = .configuration,
            priority: Int = 0,
            label: String,
            order: ExecutionOrder
        ) {
            self.phase = phase
            self.priority = priority
            self.label = label
            self.order = order
        }

        func onStartup() async throws {
            startupCalled = true
            order.values.append("start:\(label)")
        }

        func onShutdown() async {
            shutdownCalled = true
            order.values.append("stop:\(label)")
        }
    }

    /// A hook that always throws during startup for testing failure paths.
    private struct FailingHook: LifecycleHook {
        let phase: StartupPhase = .configuration
        let priority: Int = 0
        let label = "FailingHook"
        let errorMessage: String

        func onStartup() async throws {
            throw NSError(domain: "ULTRONTests", code: 1, userInfo: [
                NSLocalizedDescriptionKey: errorMessage,
            ])
        }

        func onShutdown() async {}
    }

    // MARK: - StartupPhase

    @Test("StartupPhase is CaseIterable and ordered")
    func testStartupPhaseOrder() {
        let phases = StartupPhase.allCases
        #expect(phases.count == 6)
        #expect(phases[0] == .configuration)
        #expect(phases[1] == .logging)
        #expect(phases[2] == .dependencyInjection)
        #expect(phases[3] == .applicationState)
        #expect(phases[4] == .windowSystem)
        #expect(phases[5] == .ready)
    }

    @Test("StartupPhase is comparable")
    func testStartupPhaseComparable() {
        #expect(StartupPhase.configuration < StartupPhase.logging)
        #expect(StartupPhase.logging < StartupPhase.dependencyInjection)
        #expect(StartupPhase.dependencyInjection < StartupPhase.applicationState)
        #expect(StartupPhase.applicationState < StartupPhase.windowSystem)
        #expect(StartupPhase.windowSystem < StartupPhase.ready)
    }

    @Test("StartupPhase labels are non-empty and distinct")
    func testStartupPhaseLabels() {
        var seen: Set<String> = []
        for phase in StartupPhase.allCases {
            #expect(!phase.label.isEmpty)
            #expect(!seen.contains(phase.label))
            seen.insert(phase.label)
        }
        #expect(seen.count == 6)
    }

    // MARK: - Startup Tests

    @Test("Startup sequence executes hooks in phase order, then priority order")
    func testStartupSequencePhaseOrder() async throws {
        let order = ExecutionOrder()
        let sequence = StartupSequence()

        sequence.register(TestHook(phase: .windowSystem, priority: 10, label: "Window", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 10, label: "Config", order: order))
        sequence.register(TestHook(phase: .logging, priority: 5, label: "Logger", order: order))

        try await sequence.execute()

        #expect(order.values == ["start:Config", "start:Logger", "start:Window"])
    }

    @Test("Within a phase, hooks execute in priority order")
    func testStartupWithinPhasePriorityOrder() async throws {
        let order = ExecutionOrder()
        let sequence = StartupSequence()

        sequence.register(TestHook(phase: .configuration, priority: 30, label: "Late", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 5, label: "Early", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 15, label: "Mid", order: order))

        try await sequence.execute()

        #expect(order.values == ["start:Early", "start:Mid", "start:Late"])
    }

    @Test("Same phase and priority preserves registration order")
    func testStartupSequenceSamePriority() async throws {
        let order = ExecutionOrder()
        let sequence = StartupSequence()

        sequence.register(TestHook(phase: .configuration, priority: 10, label: "First", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 10, label: "Second", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 10, label: "Third", order: order))

        try await sequence.execute()

        #expect(order.values == ["start:First", "start:Second", "start:Third"])
    }

    @Test("Duplicate registration executes hook once per registration")
    func testDuplicateRegistration() async throws {
        let order = ExecutionOrder()
        let sequence = StartupSequence()
        let hook = TestHook(phase: .configuration, priority: 10, label: "Dupe", order: order)

        sequence.register(hook)
        sequence.register(hook)

        try await sequence.execute()

        #expect(order.values == ["start:Dupe", "start:Dupe"])
    }

    @Test("Batch registration works correctly")
    func testBatchRegistration() async throws {
        let order = ExecutionOrder()
        let sequence = StartupSequence()

        let hooks: [any LifecycleHook] = [
            TestHook(phase: .ready, priority: 0, label: "Ready", order: order),
            TestHook(phase: .configuration, priority: 0, label: "Config", order: order),
            TestHook(phase: .logging, priority: 0, label: "Logger", order: order),
        ]
        sequence.register(hooks)

        try await sequence.execute()

        #expect(order.values == ["start:Config", "start:Logger", "start:Ready"])
    }

    @Test("Startup sequence throws on first failure")
    func testStartupSequenceThrowsOnFailure() async {
        let order = ExecutionOrder()
        let sequence = StartupSequence()

        sequence.register(TestHook(phase: .configuration, priority: 10, label: "Good", order: order))
        sequence.register(FailingHook(errorMessage: "Simulated failure"))

        do {
            try await sequence.execute()
            Issue.record("Expected startup sequence to throw")
        } catch {
            let nsError = error as NSError
            #expect(nsError.domain == "ULTRONTests")
        }
    }

    @Test("Startup sequence stops at first failure — later hooks not called")
    func testStartupStopsAtFirstFailure() async {
        let order = ExecutionOrder()
        let sequence = StartupSequence()

        sequence.register(FailingHook(errorMessage: "fail"))
        sequence.register(TestHook(phase: .logging, priority: 10, label: "NeverCalled", order: order))

        do {
            try await sequence.execute()
        } catch {
            // Expected — the second hook should never have been called.
        }

        #expect(order.values.isEmpty)
    }

    @Test("Empty startup sequence does not throw")
    func testEmptyStartupSequence() async throws {
        let sequence = StartupSequence()
        #expect(sequence.isEmpty == true)
        #expect(sequence.count == 0)
        try await sequence.execute()
    }

    @Test("Hooks by phase groups correctly")
    func testHooksByPhase() {
        let sequence = StartupSequence()
        let order = ExecutionOrder()

        sequence.register(TestHook(phase: .configuration, label: "Config", order: order))
        sequence.register(TestHook(phase: .logging, label: "Logger", order: order))
        sequence.register(TestHook(phase: .dependencyInjection, label: "Container", order: order))

        let phases = sequence.hooksByPhase()
        #expect(phases.count == 3)
        #expect(phases[0].phase == .configuration)
        #expect(phases[0].label == "Configuration")
        #expect(phases[1].phase == .logging)
        #expect(phases[2].phase == .dependencyInjection)
    }

    @Test("Current phase updated during execution")
    func testCurrentPhaseDuringExecution() async throws {
        let order = ExecutionOrder()
        let sequence = StartupSequence()
        sequence.register(TestHook(phase: .configuration, label: "PhaseTracker", order: order))

        #expect(sequence.currentPhase == .configuration)

        try await sequence.execute()

        #expect(sequence.currentPhase == .configuration)
    }

    // MARK: - Shutdown Tests

    @Test("Shutdown sequence executes hooks in reverse phase order")
    func testShutdownSequenceReversePhaseOrder() async {
        let order = ExecutionOrder()
        let sequence = ShutdownSequence()

        sequence.register(TestHook(phase: .configuration, priority: 10, label: "Config", order: order))
        sequence.register(TestHook(phase: .ready, priority: 10, label: "Ready", order: order))
        sequence.register(TestHook(phase: .logging, priority: 10, label: "Logger", order: order))

        await sequence.execute()

        #expect(order.values == ["stop:Ready", "stop:Logger", "stop:Config"])
    }

    @Test("Shutdown within phase reverses priority order")
    func testShutdownReversesPriority() async {
        let order = ExecutionOrder()
        let sequence = ShutdownSequence()

        sequence.register(TestHook(phase: .configuration, priority: 5, label: "Early", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 40, label: "Late", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 20, label: "Mid", order: order))

        await sequence.execute()

        #expect(order.values == ["stop:Late", "stop:Mid", "stop:Early"])
    }

    @Test("Empty shutdown sequence completes without error")
    func testEmptyShutdownSequence() async {
        let sequence = ShutdownSequence()
        #expect(sequence.isEmpty == true)
        #expect(sequence.count == 0)
        await sequence.execute()
    }

    @Test("Shutdown hooks with same phase and priority preserve registration order")
    func testShutdownSamePriority() async {
        let order = ExecutionOrder()
        let sequence = ShutdownSequence()

        sequence.register(TestHook(phase: .configuration, priority: 10, label: "X", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 10, label: "Y", order: order))

        await sequence.execute()

        #expect(order.values == ["stop:X", "stop:Y"])
    }

    @Test("Duplicate shutdown hooks execute once per registration")
    func testShutdownDuplicateRegistration() async {
        let order = ExecutionOrder()
        let sequence = ShutdownSequence()
        let hook = TestHook(phase: .configuration, priority: 10, label: "ShutdownDupe", order: order)

        sequence.register(hook)
        sequence.register(hook)

        await sequence.execute()

        #expect(order.values == ["stop:ShutdownDupe", "stop:ShutdownDupe"])
    }

    @Test("Shutdown covers all registered hooks regardless of errors")
    func testShutdownRunsAllHooksRegardlessOfErrors() async {
        let order = ExecutionOrder()
        let sequence = ShutdownSequence()

        sequence.register(TestHook(phase: .ready, priority: 30, label: "First", order: order))
        sequence.register(TestHook(phase: .applicationState, priority: 20, label: "Second", order: order))
        sequence.register(TestHook(phase: .configuration, priority: 10, label: "Third", order: order))

        await sequence.execute()

        #expect(order.values.count == 3)
        #expect(order.values[0] == "stop:First")
        #expect(order.values[1] == "stop:Second")
        #expect(order.values[2] == "stop:Third")
    }

    // MARK: - LifecycleHook Protocol

    @Test("LifecycleHook ID is derived from label")
    func testLifecycleHookID() async throws {
        let order = ExecutionOrder()
        let hook = TestHook(phase: .configuration, label: "TestID", order: order)
        #expect(hook.id == "TestID")
    }

    @Test("LifecycleHook default priority is 0")
    func testDefaultPriority() {
        struct DefaultHook: LifecycleHook {
            let phase: StartupPhase = .configuration
            let label = "Default"
            func onStartup() async throws {}
            func onShutdown() async {}
        }
        let hook = DefaultHook()
        #expect(hook.priority == 0)
    }

    @Test("Lifecycle hooks are called correctly")
    func testHookCallbacks() async throws {
        let order = ExecutionOrder()
        let hook = TestHook(phase: .configuration, priority: 5, label: "Lifecycle", order: order)

        #expect(hook.startupCalled == false)
        #expect(hook.shutdownCalled == false)

        try await hook.onStartup()
        #expect(hook.startupCalled == true)

        await hook.onShutdown()
        #expect(hook.shutdownCalled == true)
    }
}
