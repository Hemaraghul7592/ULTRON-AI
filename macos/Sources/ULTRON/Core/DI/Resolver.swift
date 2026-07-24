/// Protocol for resolving dependencies within factory closures.
///
/// Factory closures receive a `Resolver` — never the full container.
/// This prevents the service locator anti-pattern by ensuring that
/// services cannot register new types or inspect container state.
/// They can only resolve their declared dependencies.
public protocol Resolver: AnyObject {

    /// Resolves a registered service, throwing if not found.
    ///
    /// - Parameter type: The type to resolve.
    /// - Returns: The resolved service instance.
    /// - Throws: `ContainerError` if the type is not registered or
    ///   a circular dependency is detected.
    func resolve<Service>(_ type: Service.Type) async throws -> Service

    /// Resolves a registered service, returning nil if not found.
    ///
    /// - Parameter type: The type to resolve.
    /// - Returns: The resolved service instance, or nil if not registered.
    func resolveIfRegistered<Service>(_ type: Service.Type) async -> Service?
}
