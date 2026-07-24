import Foundation
import Testing

@testable import ULTRON

// MARK: - Test Service Types

private struct ServiceAlpha {
    let name: String
}

private struct ServiceBeta {
    let id: Int
}

private struct ServiceGamma {
    init() {}
}

private struct FailingService {
    init() throws {
        throw NSError(domain: "fail", code: 1)
    }
}

private struct DependentAlpha {
    let beta: ServiceBeta
}

// MARK: - ContainerDiagnostics Tests

@MainActor
@Suite struct ContainerDiagnosticsTests {

    // MARK: - validate()

    @Test("validate succeeds when all singletons are resolvable")
    func testValidateSucceeds() async throws {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self, lifetime: .singleton) { _ in
            ServiceAlpha(name: "ok")
        }
        container.register(ServiceGamma.self, lifetime: .singleton) { _ in
            ServiceGamma()
        }

        let diag = ContainerDiagnostics(container: container)
        try await diag.validate()
    }

    @Test("validate stops on first singleton failure")
    func testValidateStopsOnFailure() async {
        let container = DependencyContainer()
        container.register(FailingService.self, lifetime: .singleton) { _ in
            try FailingService()
        }
        // This service would succeed but should never be reached
        container.register(ServiceAlpha.self, lifetime: .singleton) { _ in
            ServiceAlpha(name: "unreached")
        }

        let diag = ContainerDiagnostics(container: container)
        do {
            try await diag.validate()
            Issue.record("Expected validation to fail")
        } catch {
            // Expected — FailingService factory throws
        }
    }

    @Test("validate skips transient services")
    func testValidateSkipsTransient() async throws {
        let container = DependencyContainer()
        container.register(FailingService.self, lifetime: .transient) { _ in
            try FailingService()
        }

        let diag = ContainerDiagnostics(container: container)
        // Should succeed because FailingService is transient and skipped
        try await diag.validate()
    }

    @Test("validate handles empty container")
    func testValidateEmpty() async throws {
        let container = DependencyContainer()
        let diag = ContainerDiagnostics(container: container)
        try await diag.validate()
    }

    @Test("validate exercises the canonical resolution pipeline")
    func testValidateExercisesCanonicalPipeline() async throws {
        let container = DependencyContainer()

        // Service A depends on Service B. Both go through the same
        // _resolveCore pipeline — factory execution, cycle detection,
        // singleton caching — as production resolution.
        container.register(ServiceBeta.self, lifetime: .singleton) { _ in
            ServiceBeta(id: 42)
        }
        container.register(ServiceAlpha.self, lifetime: .singleton) { resolver in
            let beta = try await resolver.resolve(ServiceBeta.self)
            return ServiceAlpha(name: "alpha-\(beta.id)")
        }

        let diag = ContainerDiagnostics(container: container)
        try await diag.validate()

        // Since validation uses the canonical pipeline, singletons
        // resolved during validation are cached (same as production).
        let records = container.diagnosticsRecords
        let beta = records.first { record in
            record.registration.typeName.contains("ServiceBeta")
        }
        // ServiceBeta was resolved as a dependency during validation
        // and cached by _resolveCore's singleton logic.
        #expect(beta?.cachedInstance != nil)
    }

    @Test("validate detects circular dependencies through real pipeline")
    func testValidateDetectsCircularDependencies() async {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self, lifetime: .singleton) { resolver in
            _ = try await resolver.resolve(ServiceBeta.self)
            return ServiceAlpha(name: "never")
        }
        container.register(ServiceBeta.self, lifetime: .singleton) { resolver in
            _ = try await resolver.resolve(ServiceAlpha.self)
            return ServiceBeta(id: 0)
        }

        let diag = ContainerDiagnostics(container: container)
        do {
            try await diag.validate()
            Issue.record("Expected circular dependency error from real pipeline")
        } catch let error as ContainerError {
            guard case .circularDependency = error else {
                Issue.record("Expected .circularDependency, got \(error)")
                return
            }
            // Cycle detected through the real resolution pipeline
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("validate uses canonical pipeline — singleton caching is active")
    func testValidateUsesCanonicalPipeline() async throws {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self, lifetime: .singleton) { _ in
            ServiceAlpha(name: "validate-test")
        }

        let diag = ContainerDiagnostics(container: container)
        try await diag.validate()

        // The canonical _resolveCore pipeline caches singletons.
        // Validation exercises the same code path as production.
        let records = container.diagnosticsRecords
        let alpha = records.first { record in
            record.registration.typeName.contains("ServiceAlpha")
        }
        #expect(alpha?.cachedInstance != nil)
    }

    @Test("validate propagates factory failure with service identity")
    func testValidatePropagatesFactoryFailure() async {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self, lifetime: .singleton) { _ in
            throw NSError(domain: "init-failure", code: 1)
        }

        let diag = ContainerDiagnostics(container: container)
        do {
            try await diag.validate()
            Issue.record("Expected validation to fail")
        } catch let error as ContainerError {
            guard case .factoryFailed(let typeName, let underlying) = error else {
                Issue.record("Expected .factoryFailed, got \(error)")
                return
            }
            #expect(typeName.contains("ServiceAlpha"))
            #expect((underlying as NSError).domain == "init-failure")
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("validate calls factory exactly once per singleton via canonical pipeline")
    func testValidateFactoryCalledOnce() async throws {
        final class Counter { var runs = 0 }
        let counter = Counter()
        let container = DependencyContainer()
        container.register(ServiceAlpha.self, lifetime: .singleton) { _ in
            counter.runs += 1
            return ServiceAlpha(name: "ok")
        }

        let diag = ContainerDiagnostics(container: container)
        try await diag.validate()

        // Factory should run exactly once — the canonical _resolveCore
        // pipeline caches singletons after the first resolution.
        #expect(counter.runs == 1)
    }

    // MARK: - registeredTypes()

    @Test("registeredTypes is sorted by registration index")
    func testRegisteredTypesSorted() {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "first") }
        container.register(ServiceBeta.self) { _ in ServiceBeta(id: 2) }
        container.register(ServiceGamma.self) { _ in ServiceGamma() }

        let diag = ContainerDiagnostics(container: container)
        let types = diag.registeredTypes()

        #expect(types.count == 3)
        #expect(types[0].registrationIndex < types[1].registrationIndex)
        #expect(types[1].registrationIndex < types[2].registrationIndex)
    }

    @Test("registeredTypes includes lifetime information")
    func testRegisteredTypesLifetime() {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self, lifetime: .singleton) { _ in ServiceAlpha(name: "s") }
        container.register(ServiceBeta.self, lifetime: .transient) { _ in ServiceBeta(id: 1) }

        let diag = ContainerDiagnostics(container: container)
        let types = diag.registeredTypes()

        #expect(types.count == 2)
        // First registered was singleton
        if case .singleton = types[0].lifetime {
            // Expected
        } else {
            Issue.record("Expected first registration to be singleton")
        }
    }

    @Test("registeredTypes excludes overwritten registrations")
    func testRegisteredTypesExcludesOverwritten() {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "v1") }
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "v2") }

        let diag = ContainerDiagnostics(container: container)
        let types = diag.registeredTypes()

        #expect(types.count == 1)
        #expect(types[0].registrationIndex == 2)
    }

    @Test("registeredTypes returns empty for unused container")
    func testRegisteredTypesEmpty() {
        let container = DependencyContainer()
        let diag = ContainerDiagnostics(container: container)
        #expect(diag.registeredTypes().isEmpty)
    }

    // MARK: - dependencyGraph()

    @Test("dependencyGraph returns entries for each registered type")
    func testDependencyGraphAllEntries() async {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "a") }
        container.register(ServiceBeta.self) { _ in ServiceBeta(id: 1) }
        container.register(ServiceGamma.self) { _ in ServiceGamma() }

        let diag = ContainerDiagnostics(container: container)
        let graph = await diag.dependencyGraph()

        #expect(graph.count == 3)
    }

    @Test("dependencyGraph detects dependencies from factory closures")
    func testDependencyGraphDetectsDependencies() async {
        let container = DependencyContainer()
        container.register(DependentAlpha.self) { resolver in
            let beta = try await resolver.resolve(ServiceBeta.self)
            return DependentAlpha(beta: beta)
        }

        let diag = ContainerDiagnostics(container: container)
        let graph = await diag.dependencyGraph()

        #expect(graph.count >= 1)
        let dependent = graph.first { $0.service.contains("DependentAlpha") }
        #expect(dependent != nil)
        #expect(dependent?.dependencies.contains(where: { $0.contains("ServiceBeta") }) == true)
    }

    @Test("dependencyGraph is deterministic across calls")
    func testDependencyGraphDeterministic() async {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "a") }
        container.register(ServiceBeta.self) { _ in ServiceBeta(id: 1) }

        let diag = ContainerDiagnostics(container: container)
        let first = await diag.dependencyGraph()
        let second = await diag.dependencyGraph()

        #expect(first.count == second.count)
        for i in 0..<first.count {
            #expect(first[i].service == second[i].service)
        }
    }

    @Test("dependencyGraph handles empty container")
    func testDependencyGraphEmpty() async {
        let container = DependencyContainer()
        let diag = ContainerDiagnostics(container: container)
        let graph = await diag.dependencyGraph()

        #expect(graph.isEmpty)
    }

    // MARK: - totalRegistrations()

    @Test("totalRegistrations reports correct active and total counts")
    func testRegistrationStatistics() {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "a") }
        container.register(ServiceBeta.self) { _ in ServiceBeta(id: 1) }

        let diag = ContainerDiagnostics(container: container)
        let stats = diag.totalRegistrations()

        #expect(stats.activeCount == 2)
        #expect(stats.totalCount == 2)
        #expect(stats.overwrittenCount == 0)
        #expect(stats.hasOverwrites == false)
    }

    @Test("totalRegistrations detects overwrites")
    func testRegistrationStatisticsOverwrites() {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "v1") }
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "v2") }
        container.register(ServiceBeta.self) { _ in ServiceBeta(id: 1) }

        let diag = ContainerDiagnostics(container: container)
        let stats = diag.totalRegistrations()

        #expect(stats.activeCount == 2)
        #expect(stats.totalCount == 3)
        #expect(stats.overwrittenCount == 1)
        #expect(stats.hasOverwrites == true)
    }

    @Test("totalRegistrations returns zeroes for empty container")
    func testRegistrationStatisticsEmpty() {
        let container = DependencyContainer()
        let diag = ContainerDiagnostics(container: container)
        let stats = diag.totalRegistrations()

        #expect(stats.activeCount == 0)
        #expect(stats.totalCount == 0)
        #expect(stats.overwrittenCount == 0)
    }

    // MARK: - Non-mutation

    @Test("diagnostics do not mutate container state")
    func testDiagnosticsDoNotMutate() async throws {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self, lifetime: .singleton) { _ in
            ServiceAlpha(name: "original")
        }

        let diag = ContainerDiagnostics(container: container)
        let before = container.registrationCount
        let beforeStats = diag.totalRegistrations()

        try await diag.validate()
        _ = diag.registeredTypes()
        _ = await diag.dependencyGraph()
        _ = diag.totalRegistrations()

        let after = container.registrationCount
        let afterStats = diag.totalRegistrations()

        #expect(before == after)
        #expect(beforeStats.activeCount == afterStats.activeCount)
        #expect(beforeStats.totalCount == afterStats.totalCount)
    }

    @Test("repeated diagnostics produce identical output")
    func testRepeatedDiagnosticsIdentical() {
        let container = DependencyContainer()
        container.register(ServiceAlpha.self) { _ in ServiceAlpha(name: "a") }
        container.register(ServiceBeta.self) { _ in ServiceBeta(id: 1) }

        let diag = ContainerDiagnostics(container: container)

        let first = diag.registeredTypes()
        let second = diag.registeredTypes()

        #expect(first.count == second.count)
        for i in 0..<first.count {
            #expect(first[i].registrationIndex == second[i].registrationIndex)
            #expect(first[i].typeName == second[i].typeName)
        }
    }
}
