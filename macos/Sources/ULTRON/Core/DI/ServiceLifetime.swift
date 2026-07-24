/// Determines how long a registered service lives within the container.
///
/// `ServiceLifetime` controls whether the container creates a single shared
/// instance or a new instance on every resolution request.
///
/// ## Future Extensibility
///
/// The `scoped` case is reserved for a future milestone where services
/// need lifetimes tied to a specific scope (e.g., per-request, per-session).
/// When implemented, it will not require changes to existing registration
/// or resolution APIs.
public enum ServiceLifetime: Sendable {

    /// Created once and cached. Every subsequent resolution returns the
    /// same instance. Use for stateless services, shared resources, and
    /// services with expensive initialization.
    case singleton

    /// Created fresh on every resolution. Use for services that hold
    /// request-specific state or cannot be safely shared.
    case transient

    /// Reserved for future: lifetime tied to a configurable scope.
    /// Do not use. Will be implemented in a future milestone.
    // case scoped
}
