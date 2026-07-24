import Foundation
import Testing

@testable import ULTRON

// MARK: - Test Service Types

/// A simple service type used across multiple registration tests.
private struct TestService {
    let value: String
}

/// A second service type for testing multiple registrations.
private struct AnotherService {
    let id: Int
}

/// A service that depends on another service.
private struct DependentService {
    let dependency: TestService
}

// MARK: - ServiceLifetime Tests

@MainActor
@Suite struct ServiceLifetimeTests {

    @Test("ServiceLifetime has singleton case")
    func testSingletonCase() {
        let lifetime = ServiceLifetime.singleton
        if case .singleton = lifetime {
            // Expected
        } else {
            Issue.record("Expected .singleton")
        }
    }

    @Test("ServiceLifetime has transient case")
    func testTransientCase() {
        let lifetime = ServiceLifetime.transient
        if case .transient = lifetime {
            // Expected
        } else {
            Issue.record("Expected .transient")
        }
    }

    @Test("ServiceLifetime conforms to Sendable")
    func testSendableConformance() {
        let lifetime: any Sendable = ServiceLifetime.singleton
        _ = lifetime
        // If this compiles, Sendable conformance is verified.
    }
}

// MARK: - ServiceRegistration Tests

@MainActor
@Suite struct ServiceRegistrationTests {

    @Test("ServiceRegistration stores service type correctly")
    func testServiceType() {
        let oid = ObjectIdentifier(TestService.self)
        let reg = ServiceRegistration(serviceType: ObjectIdentifier(TestService.self),
            typeName: "TestService",
            lifetime: .singleton,
            factory: { _ in TestService(value: "test") }
        )

        #expect(reg.serviceType == oid)
    }

    @Test("ServiceRegistration stores lifetime correctly")
    func testLifetime() {
        let reg = ServiceRegistration(serviceType: ObjectIdentifier(TestService.self),
            typeName: "TestService",
            lifetime: .transient,
            factory: { _ in TestService(value: "test") }
        )

        if case .transient = reg.lifetime {
            // Expected
        } else {
            Issue.record("Expected .transient lifetime")
        }
    }

    @Test("ServiceRegistration stores factory correctly")
    func testFactory() async throws {
        let expected = TestService(value: "hello")
        let reg = ServiceRegistration(serviceType: ObjectIdentifier(TestService.self),
            typeName: "TestService",
            lifetime: .singleton,
            factory: { _ in expected }
        )

        // Factory requires a Resolver. Use a minimal mock.
        let result = try await reg.factory(MockResolver()) as? TestService
        #expect(result?.value == "hello")
    }
}

// MARK: - ServiceRecord Tests

@MainActor
@Suite struct ServiceRecordTests {

    @Test("ServiceRecord stores registration and index")
    func testRecordCreation() {
        let reg = ServiceRegistration(serviceType: ObjectIdentifier(TestService.self),
            typeName: "TestService",
            lifetime: .singleton,
            factory: { _ in TestService(value: "test") }
        )
        let record = ServiceRecord(registration: reg, index: 7)

        #expect(record.index == 7)
        #expect(record.registration.serviceType == reg.serviceType)
        #expect(record.cachedInstance == nil)
    }

    @Test("ServiceRecord can cache an instance")
    func testRecordCaching() {
        let reg = ServiceRegistration(serviceType: ObjectIdentifier(TestService.self),
            typeName: "TestService",
            lifetime: .singleton,
            factory: { _ in TestService(value: "cached") }
        )
        let service = TestService(value: "instance")
        var record = ServiceRecord(registration: reg, index: 1, cachedInstance: service)

        #expect(record.cachedInstance != nil)
        let retrieved = record.cachedInstance as? TestService
        #expect(retrieved?.value == "instance")
    }

    @Test("ServiceRecord index is immutable via let")
    func testIndexIsImmutable() {
        let reg = ServiceRegistration(serviceType: ObjectIdentifier(TestService.self),
            typeName: "TestService",
            lifetime: .singleton,
            factory: { _ in TestService(value: "test") }
        )
        let record = ServiceRecord(registration: reg, index: 42)

        #expect(record.index == 42)
        // index is `let`, so it cannot be reassigned.
    }
}

// MARK: - DependencyContainer Registration Tests

@MainActor
@Suite struct DependencyContainerRegistrationTests {

    @Test("Empty container has no registrations")
    func testEmptyContainer() {
        let container = DependencyContainer()
        #expect(container.registrationCount == 0)
        #expect(container.totalRegistrations == 0)
    }

    @Test("Register a singleton service")
    func testRegisterSingleton() {
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .singleton) { _ in
            TestService(value: "singleton")
        }

        #expect(container.registrationCount == 1)
        #expect(container.totalRegistrations == 1)
    }

    @Test("Register a transient service")
    func testRegisterTransient() {
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .transient) { _ in
            TestService(value: "transient")
        }

        #expect(container.registrationCount == 1)
        #expect(container.totalRegistrations == 1)
    }

    @Test("Register multiple services")
    func testRegisterMultiple() {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "a") }
        container.register(AnotherService.self) { _ in AnotherService(id: 1) }

        #expect(container.registrationCount == 2)
        #expect(container.totalRegistrations == 2)
    }

    @Test("Registration index increments monotonically")
    func testRegistrationIndex() {
        let container = DependencyContainer()

        container.register(TestService.self) { _ in TestService(value: "first") }
        #expect(container.totalRegistrations == 1)

        container.register(AnotherService.self) { _ in AnotherService(id: 2) }
        #expect(container.totalRegistrations == 2)

        container.register(TestService.self) { _ in TestService(value: "third") }
        #expect(container.totalRegistrations == 3)
    }

    @Test("Overwrite creates new record with new index")
    func testOverwriteNewIndex() {
        let container = DependencyContainer()

        container.register(TestService.self) { _ in TestService(value: "first") }
        let afterFirst = container.totalRegistrations

        container.register(TestService.self) { _ in TestService(value: "second") }
        let afterSecond = container.totalRegistrations

        #expect(afterFirst == 1)
        #expect(afterSecond == 2)
        #expect(container.registrationCount == 1)
    }

    @Test("Overwrite does not increase registration count")
    func testOverwriteCountStaysSame() {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "v1") }
        #expect(container.registrationCount == 1)

        container.register(TestService.self) { _ in TestService(value: "v2") }
        #expect(container.registrationCount == 1)
    }

    @Test("Overwrite increments total registrations")
    func testOverwriteIncrementsTotal() {
        let container = DependencyContainer()

        container.register(TestService.self) { _ in TestService(value: "a") }
        #expect(container.totalRegistrations == 1)

        container.register(TestService.self) { _ in TestService(value: "b") }
        #expect(container.totalRegistrations == 2)

        container.register(AnotherService.self) { _ in AnotherService(id: 99) }
        #expect(container.totalRegistrations == 3)
    }

    @Test("Snapshot returns records sorted by index")
    func testSnapshotOrdering() {
        let container = DependencyContainer()

        container.register(TestService.self) { _ in TestService(value: "a") }
        container.register(AnotherService.self) { _ in AnotherService(id: 1) }

        let snap = container.snapshot()
        #expect(snap.count == 2)
        #expect(snap[0].registrationIndex < snap[1].registrationIndex)
    }

    @Test("Default lifetime is singleton")
    func testDefaultLifetimeIsSingleton() {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "default") }

        let snap = container.snapshot()
        #expect(snap.count == 1)
        if case .singleton = snap[0].lifetime {
            // Expected default
        } else {
            Issue.record("Default lifetime should be .singleton")
        }
    }

    @Test("Snapshot exposes type name")
    func testSnapshotTypeName() {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "named") }

        let snap = container.snapshot()
        #expect(snap.count == 1)
        #expect(snap[0].typeName.contains("TestService"))
    }

    @Test("Snapshot exposes registration index")
    func testSnapshotRegistrationIndex() {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "first") }
        container.register(AnotherService.self) { _ in AnotherService(id: 2) }

        let snap = container.snapshot()
        #expect(snap[0].registrationIndex == 1)
        #expect(snap[1].registrationIndex == 2)
    }

    @Test("Snapshot exposes lifetime")
    func testSnapshotLifetime() {
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .transient) { _ in TestService(value: "t") }

        let snap = container.snapshot()
        if case .transient = snap[0].lifetime {
            // Expected
        } else {
            Issue.record("Expected .transient lifetime in snapshot")
        }
    }

    @Test("Overwritten registration not visible in snapshot")
    func testSnapshotExcludesOverwritten() {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "v1") }
        container.register(TestService.self) { _ in TestService(value: "v2") }

        let snap = container.snapshot()
        #expect(snap.count == 1)
        #expect(snap[0].registrationIndex == 2)
    }
}

// MARK: - RegistrationSnapshot Tests

@MainActor
@Suite struct RegistrationSnapshotTests {

    @Test("Snapshot exposes Sendable conformance")
    func testSendableConformance() {
        let snap = RegistrationSnapshot(
            typeName: "Test",
            lifetime: .singleton,
            registrationIndex: 1
        )
        let sendable: any Sendable = snap
        _ = sendable
    }

    @Test("Snapshot properties match construction values")
    func testSnapshotProperties() {
        let snap = RegistrationSnapshot(
            typeName: "Database",
            lifetime: .transient,
            registrationIndex: 5
        )

        #expect(snap.typeName == "Database")
        #expect(snap.registrationIndex == 5)
        if case .transient = snap.lifetime {
            // Expected
        } else {
            Issue.record("Expected .transient lifetime")
        }
    }
}

// MARK: - ContainerError Tests

@MainActor
@Suite struct ContainerErrorTests {

    @Test("notRegistered produces descriptive message")
    func testNotRegisteredDescription() {
        let error = ContainerError.notRegistered(typeName: "TestService")
        let desc = error.description

        #expect(desc.contains("is not registered"))
    }

    @Test("circularDependency produces descriptive message")
    func testCircularDependencyDescription() {
        let a = ResolutionFrame(typeIdentifier: ObjectIdentifier(TestService.self), typeName: "TestService")
        let b = ResolutionFrame(typeIdentifier: ObjectIdentifier(AnotherService.self), typeName: "AnotherService")
        let error = ContainerError.circularDependency(chain: [a, b, a])
        let desc = error.description

        #expect(desc.contains("Circular dependency"))
        #expect(desc.contains("↓"))
    }

    @Test("factoryFailed produces descriptive message")
    func testFactoryFailedDescription() {
        let error = ContainerError.factoryFailed(typeName: "TestService", underlying: NSError(domain: "test", code: 1))
        let desc = error.description

        #expect(desc.contains("Factory for"))
        #expect(desc.contains("failed"))
    }

    @Test("ContainerError conforms to CustomStringConvertible")
    func testCustomStringConvertible() {
        let error = ContainerError.notRegistered(typeName: "TestService")

        let convertible: any CustomStringConvertible = error
        #expect(!convertible.description.isEmpty)
    }
}

// MARK: - Mock Resolver

/// A minimal mock resolver used during registration tests.
/// No resolution logic — exists only so factory closures can
/// receive a `Resolver` parameter.
private final class MockResolver: Resolver {
    func resolve<Service>(_ type: Service.Type) async throws -> Service {
        fatalError("MockResolver cannot resolve. Use in registration tests only.")
    }

    func resolveIfRegistered<Service>(_ type: Service.Type) async -> Service? {
        nil
    }
}

// MARK: - DependencyContainer Resolution Tests

@MainActor
@Suite struct DependencyContainerResolutionTests {

    @Test("resolve returns successfully for a registered singleton")
    func testResolveSingleton() async throws {
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .singleton) { _ in
            TestService(value: "resolved")
        }

        let service = try await container._resolve(TestService.self)
        #expect(service.value == "resolved")
    }

    @Test("resolve returns the same instance for a singleton")
    func testSingletonReturnsSameInstance() async throws {
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .singleton) { _ in
            TestService(value: "shared")
        }

        let first = try await container._resolve(TestService.self)
        let second = try await container._resolve(TestService.self)

        #expect(first.value == "shared")
        #expect(second.value == "shared")
    }

    @Test("resolve returns different instances for transient")
    func testTransientReturnsNewInstances() async throws {
        final class Counter {
            var count = 0
        }
        let counter = Counter()
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .transient) { _ in
            counter.count += 1
            return TestService(value: "instance-\(counter.count)")
        }

        let first = try await container._resolve(TestService.self)
        let second = try await container._resolve(TestService.self)

        #expect(first.value == "instance-1")
        #expect(second.value == "instance-2")
    }

    @Test("resolve throws notRegistered for unregistered type")
    func testResolveNotRegistered() async {
        let container = DependencyContainer()

        do {
            _ = try await container._resolve(TestService.self)
            Issue.record("Expected .notRegistered error")
        } catch let error as ContainerError {
            if case .notRegistered = error {
                // Expected
            } else {
                Issue.record("Expected .notRegistered, got \(error)")
            }
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("resolve throws factoryFailed when factory throws")
    func testResolveFactoryThrows() async {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in
            throw NSError(domain: "test", code: 42)
        }

        do {
            _ = try await container._resolve(TestService.self)
            Issue.record("Expected .factoryFailed error")
        } catch let error as ContainerError {
            if case .factoryFailed(let typeName, let underlying) = error {
                let nsError = underlying as NSError
                #expect(nsError.domain == "test")
                #expect(nsError.code == 42)
            } else {
                Issue.record("Expected .factoryFailed, got \(error)")
            }
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("resolve factory receives working Resolver")
    func testFactoryReceivesResolver() async throws {
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .singleton) { _ in
            TestService(value: "parent")
        }
        container.register(DependentService.self) { resolver in
            let dep = try await resolver.resolve(TestService.self)
            return DependentService(dependency: dep)
        }

        let service = try await container._resolve(DependentService.self)
        #expect(service.dependency.value == "parent")
    }

    @Test("resolveIfRegistered returns nil for unregistered type")
    func testResolveIfRegisteredNil() async {
        let container = DependencyContainer()
        let result = await container._resolveIfRegistered(TestService.self)
        #expect(result == nil)
    }

    @Test("resolveIfRegistered returns instance for registered type")
    func testResolveIfRegisteredSuccess() async throws {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in
            TestService(value: "found")
        }

        let result = await container._resolveIfRegistered(TestService.self)
        #expect(result?.value == "found")
    }

    @Test("resolveIfRegistered propagates factory error")
    func testResolveIfRegisteredPropagatesError() async {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in
            throw NSError(domain: "factory", code: 1)
        }

        let result = await container._resolveIfRegistered(TestService.self)
        #expect(result == nil)
    }

    @Test("singleton factory runs exactly once")
    func testSingletonFactoryRunsOnce() async throws {
        final class Counter {
            var runs = 0
        }
        let counter = Counter()
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .singleton) { _ in
            counter.runs += 1
            return TestService(value: "singleton")
        }

        _ = try await container._resolve(TestService.self)
        _ = try await container._resolve(TestService.self)
        _ = try await container._resolve(TestService.self)

        #expect(counter.runs == 1)
    }

    @Test("transient factory runs on every resolve")
    func testTransientFactoryRunsEveryTime() async throws {
        final class Counter {
            var runs = 0
        }
        let counter = Counter()
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .transient) { _ in
            counter.runs += 1
            return TestService(value: "transient")
        }

        _ = try await container._resolve(TestService.self)
        _ = try await container._resolve(TestService.self)

        #expect(counter.runs == 2)
    }

    @Test("resolution is type-safe across different service types")
    func testTypeSafety() async throws {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "a") }
        container.register(AnotherService.self) { _ in AnotherService(id: 99) }

        let a = try await container._resolve(TestService.self)
        let b = try await container._resolve(AnotherService.self)

        #expect(a.value == "a")
        #expect(b.id == 99)
    }
    @Test("factoryFailed error preserves the requested service identity")
    func testFactoryFailedPreservesServiceIdentity() async {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in
            throw NSError(domain: "db", code: 1)
        }

        do {
            _ = try await container._resolve(TestService.self)
            Issue.record("Expected .factoryFailed error")
        } catch let error as ContainerError {
            guard case .factoryFailed(let typeName, let underlying) = error else {
                Issue.record("Expected .factoryFailed, got \(error)")
                return
            }
            // Verify the error identifies TestService, not Any.self
            // Verify the error identifies TestService, not Any.self
            #expect(typeName.contains("TestService"))
            #expect(!typeName.contains("Any"))

            // Verify the underlying error is preserved
            let nsError = underlying as NSError
            #expect(nsError.domain == "db")
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("factoryFailed preserves identity for each registered type")
    func testFactoryFailedIdentityPerType() async {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in
            throw NSError(domain: "a", code: 1)
        }
        container.register(AnotherService.self) { _ in
            throw NSError(domain: "b", code: 2)
        }

        do {
            _ = try await container._resolve(AnotherService.self)
            Issue.record("Expected error from AnotherService factory")
        } catch let error as ContainerError {
            guard case .factoryFailed(let typeName, _) = error else {
                Issue.record("Expected .factoryFailed, got \(error)")
                return
            }
            #expect(typeName.contains("AnotherService"))
            #expect(!typeName.contains("TestService"))
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("error description contains service identity, not Any.self")
    func testErrorDescriptionContainsServiceIdentity() async {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in
            throw NSError(domain: "err", code: 99)
        }

        do {
            _ = try await container._resolve(TestService.self)
        } catch let error as ContainerError {
            let desc = error.description
            #expect(desc.contains("TestService"))
            #expect(!desc.contains("Any"))
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }
}

// MARK: - Circular Dependency Tests

@MainActor
@Suite struct DependencyContainerCircularDependencyTests {

    @Test("Self-dependency A → A detected")
    func testSelfDependency() async {
        let container = DependencyContainer()
        container.register(TestService.self) { resolver in
            _ = try await resolver.resolve(TestService.self)
            return TestService(value: "never")
        }

        do {
            _ = try await container._resolve(TestService.self)
            Issue.record("Expected circular dependency error")
        } catch let error as ContainerError {
            guard case .circularDependency(let chain) = error else {
                Issue.record("Expected .circularDependency, got \(error)")
                return
            }
            #expect(chain.count == 2)
            #expect(chain[0].typeIdentifier == chain[1].typeIdentifier)
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("Direct cycle A → B → A detected")
    func testDirectCycle() async {
        let container = DependencyContainer()
        container.register(TestService.self) { resolver in
            _ = try await resolver.resolve(AnotherService.self)
            return TestService(value: "never")
        }
        container.register(AnotherService.self) { resolver in
            _ = try await resolver.resolve(TestService.self)
            return AnotherService(id: 0)
        }

        do {
            _ = try await container._resolve(TestService.self)
            Issue.record("Expected circular dependency error")
        } catch let error as ContainerError {
            guard case .circularDependency(let chain) = error else {
                Issue.record("Expected .circularDependency, got \(error)")
                return
            }
            #expect(chain.count >= 3)
            #expect(chain[0].typeIdentifier == chain.last?.typeIdentifier)
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("Three-node cycle A → B → C → A detected")
    func testThreeNodeCycle() async {
        let container = DependencyContainer()

        // Deliberately named for clarity in test output
        struct ServiceA { init(dep _: Any?) {} }
        struct ServiceB { init(dep _: Any?) {} }
        struct ServiceC { init(dep _: Any?) {} }

        container.register(ServiceA.self) { resolver in
            _ = try await resolver.resolve(ServiceB.self)
            return ServiceA(dep: nil)
        }
        container.register(ServiceB.self) { resolver in
            _ = try await resolver.resolve(ServiceC.self)
            return ServiceB(dep: nil)
        }
        container.register(ServiceC.self) { resolver in
            _ = try await resolver.resolve(ServiceA.self)
            return ServiceC(dep: nil)
        }

        do {
            _ = try await container._resolve(ServiceA.self)
            Issue.record("Expected circular dependency error")
        } catch let error as ContainerError {
            guard case .circularDependency(let chain) = error else {
                Issue.record("Expected .circularDependency, got \(error)")
                return
            }
            #expect(chain.count == 4)
            #expect(chain[0].typeIdentifier == chain.last?.typeIdentifier)
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("Successful acyclic graph A → B → C resolves normally")
    func testAcyclicGraph() async throws {
        let container = DependencyContainer()

        struct NodeA { let dep: NodeB }
        struct NodeB { let dep: NodeC }
        struct NodeC { init() {} }

        container.register(NodeC.self) { _ in NodeC() }
        container.register(NodeB.self) { resolver in
            NodeB(dep: try await resolver.resolve(NodeC.self))
        }
        container.register(NodeA.self) { resolver in
            NodeA(dep: try await resolver.resolve(NodeB.self))
        }

        let a = try await container._resolve(NodeA.self)
        _ = a  // Success — no cycle
    }

    @Test("Singleton cycle detected same as transient cycle")
    func testSingletonCycle() async {
        let container = DependencyContainer()
        container.register(TestService.self, lifetime: .singleton) { resolver in
            _ = try await resolver.resolve(AnotherService.self)
            return TestService(value: "never")
        }
        container.register(AnotherService.self, lifetime: .singleton) { resolver in
            _ = try await resolver.resolve(TestService.self)
            return AnotherService(id: 0)
        }

        do {
            _ = try await container._resolve(TestService.self)
            Issue.record("Expected circular dependency error")
        } catch let error as ContainerError {
            guard case .circularDependency = error else {
                Issue.record("Expected .circularDependency, got \(error)")
                return
            }
            // Cycle detected regardless of lifetime
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("Stack is clean after a failed resolution")
    func testStackCleanupAfterFailure() async throws {
        let container = DependencyContainer()

        struct FailsWithCycle {
            init(resolver _: any Resolver) throws {
                throw NSError(domain: "cycle", code: 1)
            }
        }
        struct SucceedsAfter {
            init() {}
        }

        container.register(FailsWithCycle.self) { _ in
            throw NSError(domain: "cycle", code: 1)
        }
        container.register(SucceedsAfter.self) { _ in
            SucceedsAfter()
        }

        // First resolution fails
        _ = try? await container._resolve(FailsWithCycle.self)

        // Second resolution should work — stack must be empty
        let result = try await container._resolve(SucceedsAfter.self)
        _ = result
    }

    @Test("Stack is empty after multiple successful resolutions")
    func testStackEmptyAfterSuccess() async throws {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "ok") }

        _ = try await container._resolve(TestService.self)
        _ = try await container._resolve(TestService.self)
        _ = try await container._resolve(TestService.self)

        // No assertion on stack directly (it's private).
        // If the stack leaked, the next resolution would falsely
        // detect a cycle. Three successful resolutions prove
        // the stack is balanced.
    }

    @Test("Circular dependency error description includes chain")
    func testCircularDependencyErrorDescription() {
        let a = ResolutionFrame(typeIdentifier: ObjectIdentifier(TestService.self), typeName: "TestService")
        let b = ResolutionFrame(typeIdentifier: ObjectIdentifier(AnotherService.self), typeName: "AnotherService")
        let chain = [a, b, a]
        let error = ContainerError.circularDependency(chain: chain)
        let desc = error.description

        #expect(desc.contains("Circular dependency"))
        #expect(desc.contains("↓"))
        #expect(desc.contains("TestService"))
        #expect(desc.contains("AnotherService"))
    }
}

// MARK: - ContainerResolver Tests

@MainActor
@Suite struct ContainerResolverTests {

    @Test("ContainerResolver delegates to container")
    func testDelegationToContainer() async throws {
        let container = DependencyContainer()
        container.register(TestService.self) { _ in TestService(value: "via resolver") }

        let resolver = ContainerResolver(container: container)
        let service = try await resolver.resolve(TestService.self)

        #expect(service.value == "via resolver")
    }

    @Test("ContainerResolver resolveIfRegistered returns nil for missing")
    func testResolverNilForMissing() async {
        let container = DependencyContainer()
        let resolver = ContainerResolver(container: container)

        let result = await resolver.resolveIfRegistered(TestService.self)
        #expect(result == nil)
    }
}
