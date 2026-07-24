import Foundation

/// Manages the lifecycle and resolution of application-wide services.
///
/// `DependencyContainer` is the central registry for ULTRON's dependency
/// injection system. Services are registered with a lifetime policy and
/// a factory closure. The container constructs and caches services on
/// demand during resolution.
///
/// ## Thread Safety
///
/// The container is confined to `@MainActor`. Registration and resolution
/// both occur on the main actor. Services that need background-thread
/// resolution can `await` the container from any context, and the call
/// will hop to the main actor.
///
/// ## Registration Index
///
/// Every registration receives a monotonically increasing index.
/// This provides deterministic ordering for diagnostics and testing.
/// Re-registering a type creates a new record with a new index.
///
/// ## Example
/// ```swift
/// let container = DependencyContainer()
/// container.register(Database.self, lifetime: .singleton) { resolver in
///     try Database(config: resolver.resolve(Configuration.self))
/// }
/// ```
@MainActor
public final class DependencyContainer {

    // MARK: - Internal Storage

    /// All registered services, keyed by their `ObjectIdentifier`.
    /// Access is serialized by the main actor.
    private var records: [ObjectIdentifier: ServiceRecord] = [:]

    /// Monotonically increasing counter assigned to each registration.
    /// Starts at 1 so that index 0 can represent "not found" if needed.
    private var nextIndex: Int = 1

    /// Tracks the active resolution chain. Used to detect circular
    /// dependencies. Each entry records which type is currently being
    /// resolved. The stack is empty when no resolutions are in progress.
    private var resolutionStack: [ResolutionFrame] = []

    // MARK: - Initialization

    /// Creates an empty dependency container ready for registration.
    public init() {}

    // MARK: - Registration

    /// Registers a service type with the container.
    ///
    /// The factory closure is called when the service is first resolved
    /// (for singletons) or on every resolution (for transients). It
    /// receives a `Resolver` so the service can declare and resolve
    /// its own dependencies.
    ///
    /// If the type was previously registered, the old registration is
    /// replaced. The new registration receives a new index, and any
    /// cached singleton is discarded.
    ///
    /// - Parameters:
    ///   - type: The type to register. Typically passed as `Type.self`.
    ///   - lifetime: How long instances should live. Defaults to `.singleton`.
    ///   - factory: A closure that constructs the service. Receives a
    ///     `Resolver` for dependency resolution.
    public func register<Service>(
        _ type: Service.Type,
        lifetime: ServiceLifetime = .singleton,
        factory: @escaping (any Resolver) async throws -> Service
    ) {
        let oid = ObjectIdentifier(type)
        let typeName = String(describing: Service.self)
        let wrappedFactory: (any Resolver) async throws -> Any = { resolver in
            try await factory(resolver) as Any
        }
        let registration = ServiceRegistration(
            serviceType: oid,
            typeName: typeName,
            lifetime: lifetime,
            factory: wrappedFactory
        )
        let record = ServiceRecord(registration: registration, index: nextIndex)
        nextIndex += 1
        records[oid] = record
    }

    // MARK: - Resolution

    /// Resolves a registered type, returning a fully constructed instance.
    ///
    /// Delegates to the core resolution pipeline then casts the result
    /// to the requested generic type. This is the single production
    /// resolution path — all service construction flows through it.
    ///
    /// - Parameter type: The type to resolve.
    /// - Returns: The resolved service instance.
    /// - Throws: `ContainerError.notRegistered` or `.factoryFailed`.
    func _resolve<Service>(_ type: Service.Type) async throws -> Service {
        let oid = ObjectIdentifier(type)
        let instance = try await _resolveCore(for: oid)
        return try castToService(instance, as: Service.self, for: oid)
    }

    /// The canonical resolution pipeline. Every code path that constructs
    /// a service — production resolution, validation, dependency resolution —
    /// ultimately flows through this method.
    ///
    /// Steps: lookup → cache check → cycle detection → factory execution
    /// → singleton caching. No other code path duplicates this logic.
    ///
    /// - Parameter oid: The `ObjectIdentifier` of the type to resolve.
    /// - Returns: The constructed instance as `Any`.
    /// - Throws: `ContainerError` if resolution fails.
    private func _resolveCore(for oid: ObjectIdentifier) async throws -> Any {
        var record = try lookupRecord(for: oid)
        try beginResolution(of: oid, typeName: record.registration.typeName)
        defer { endResolution() }

        if let cached = record.cachedInstance {
            return cached
        }

        let instance = try await executeFactory(
            record.registration.factory,
            serviceType: oid,
            typeName: record.registration.typeName
        )

        cacheIfSingleton(&record, instance: instance, for: oid)

        return instance
    }

    /// Resolves a registered type, returning nil if not found.
    ///
    /// If the type is registered, this method delegates to `_resolve(_:)`.
    /// Factory errors from a registered type are propagated — only a
    /// missing registration produces `nil`.
    ///
    /// - Parameter type: The type to resolve.
    /// - Returns: The resolved service instance, or nil if not registered.
    /// - Throws: `ContainerError.factoryFailed` if the factory throws.
    func _resolveIfRegistered<Service>(_ type: Service.Type) async -> Service? {
        let oid = ObjectIdentifier(type)
        guard records[oid] != nil else {
            return nil
        }
        return try? await _resolve(type)
    }

    // MARK: - Resolution Helpers

    /// Looks up the `ServiceRecord` for the given type identifier.
    ///
    /// - Parameter oid: The `ObjectIdentifier` of the desired type.
    /// - Returns: The matching `ServiceRecord`.
    /// - Throws: `ContainerError.notRegistered` if no record exists.
    private func lookupRecord(for oid: ObjectIdentifier) throws -> ServiceRecord {
        guard let record = records[oid] else {
            throw ContainerError.notRegistered(typeName: String(describing: oid))
        }
        return record
    }

    /// Executes a factory closure and normalizes its error output.
    ///
    /// `ContainerError` values thrown by the factory are re-thrown
    /// as-is to preserve their diagnostic information. All other
    /// errors are wrapped in `ContainerError.factoryFailed` using
    /// the provided `serviceType` identity — never a generic
    /// placeholder.
    ///
    /// - Parameters:
    ///   - factory: The closure to execute.
    ///   - serviceType: The `ObjectIdentifier` of the registered type.
    ///     Preserved in error output so diagnostics always identify
    ///     which service failed.
    /// - Returns: The opaque instance produced by the factory.
    /// - Throws: `ContainerError` — either re-thrown from the factory
    ///   or wrapping a factory failure.
    private func executeFactory(
        _ factory: (any Resolver) async throws -> Any,
        serviceType: ObjectIdentifier,
        typeName: String
    ) async throws -> Any {
        let resolver = ContainerResolver(container: self)
        do {
            return try await factory(resolver)
        } catch let error as ContainerError {
            throw error
        } catch {
            throw ContainerError.factoryFailed(
                typeName: typeName,
                underlying: error
            )
        }
    }

    /// Casts an opaque instance to the expected `Service` type.
    ///
    /// - Parameters:
    ///   - instance: The opaque value from the factory.
    ///   - type: The expected `Service` type.
    ///   - oid: The `ObjectIdentifier` of the registered type.
    /// - Returns: The instance cast to `Service`.
    /// - Throws: `ContainerError.factoryFailed` if the cast fails.
    private func castToService<Service>(
        _ instance: Any,
        as type: Service.Type,
        for oid: ObjectIdentifier
    ) throws -> Service {
        guard let service = instance as? Service else {
            throw ContainerError.factoryFailed(
                typeName: String(describing: Service.self),
                underlying: typeMismatch(expected: Service.self)
            )
        }
        return service
    }

    /// Caches the constructed instance for future singleton resolutions.
    ///
    /// Transient registrations are silently skipped — only singletons
    /// are written to the cache. The record is written back to the
    /// `records` dictionary so the cache persists across resolutions.
    ///
    /// - Parameters:
    ///   - record: The record to update (passed `inout`).
    ///   - instance: The instance to cache.
    ///   - oid: The `ObjectIdentifier` key for the dictionary.
    private func cacheIfSingleton(
        _ record: inout ServiceRecord,
        instance: Any,
        for oid: ObjectIdentifier
    ) {
        guard case .singleton = record.registration.lifetime else {
            return
        }
        record.cachedInstance = instance
        records[oid] = record
    }

    /// Creates a type-mismatch error for diagnostic reporting.
    ///
    /// - Parameter expected: The `Service` type that was requested.
    /// - Returns: An error describing the mismatch.
    private func typeMismatch<Service>(expected: Service.Type) -> TypeMismatchError {
        TypeMismatchError(expected: String(describing: Service.self))
    }

    // MARK: - Cycle Detection

    /// Pushes the given type onto the resolution stack after verifying
    /// that it does not already appear (which would indicate a cycle).
    ///
    /// - Parameter oid: The `ObjectIdentifier` of the type being resolved.
    /// - Throws: `ContainerError.circularDependency` if `oid` is already
    ///   present in the active resolution chain.
    private func beginResolution(of oid: ObjectIdentifier, typeName: String) throws {
        let frame = ResolutionFrame(typeIdentifier: oid, typeName: typeName)
        if resolutionStack.contains(where: { $0.typeIdentifier == oid }) {
            let chain = resolutionStack + [frame]
            throw ContainerError.circularDependency(chain: chain)
        }
        resolutionStack.append(frame)
    }

    /// Pops the most recently pushed type from the resolution stack.
    ///
    /// Must be called exactly once for every successful `beginResolution`.
    /// Use `defer` in the caller to guarantee this method runs even
    /// when resolution throws.
    private func endResolution() {
        if !resolutionStack.isEmpty {
            resolutionStack.removeLast()
        }
    }

    // MARK: - Internal Error

    /// A lightweight error used when a factory returns an instance
    /// whose type does not match the registered service type.
    private struct TypeMismatchError: Error, CustomStringConvertible {
        let expected: String
        var description: String {
            "Factory returned an instance that is not a \(expected)."
        }
    }

    // MARK: - Diagnostics Support

    /// Validates a single registration by invoking the canonical
    /// resolution pipeline and discarding the result.
    ///
    /// This method contains ZERO duplicated resolution logic. It
    /// delegates entirely to `_resolveCore(for:)` — the same pipeline
    /// used by `_resolve(_:)` and every dependency resolution.
    ///
    /// - Parameter oid: The `ObjectIdentifier` of the type to validate.
    /// - Throws: `ContainerError` if resolution fails.
    func _validateRecord(for oid: ObjectIdentifier) async throws {
        _ = try await _resolveCore(for: oid)
    }

    /// Returns the number of active registrations.
    /// Excludes overwritten registrations.
    var registrationCount: Int {
        records.count
    }

    /// Returns the total number of registrations ever made,
    /// including overwrites. The next index minus one.
    var totalRegistrations: Int {
        nextIndex - 1
    }

    /// Returns a lightweight snapshot of all active registrations.
    ///
    /// Snapshots are sorted by registration index for deterministic
    /// output across runs. Each snapshot exposes only public metadata:
    /// type name, lifetime, and registration index. Internal details
    /// such as factory closures and cached instances are not exposed.
    func snapshot() -> [RegistrationSnapshot] {
        records.values
            .sorted { $0.index < $1.index }
            .map { RegistrationSnapshot(record: $0) }
    }

    /// Read-only access to registration records for diagnostics.
    /// Sorted by registration index. Must not be mutated by callers.
    var diagnosticsRecords: [ServiceRecord] {
        records.values.sorted { $0.index < $1.index }
    }
}
