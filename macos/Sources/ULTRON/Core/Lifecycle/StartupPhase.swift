/// A strongly typed startup phase that determines execution order.
///
/// Each phase represents a distinct stage of application initialization.
/// Hooks declare which phase they belong to, and the system executes
/// phases in case declaration order. Within a phase, hooks are ordered
/// by their `priority` value.
///
/// Adding a new phase requires only adding a new case — no numeric
/// ranges to manage, no risk of collision.
///
/// ## Example
/// ```swift
/// struct DatabaseHook: LifecycleHook {
///     let phase: StartupPhase = .dependencyInjection
///     let priority: Int = 10
///     let label = "Database"
///     ...
/// }
/// ```
public enum StartupPhase: Int, CaseIterable, Comparable, Sendable {

    /// Environment, build flags, runtime configuration.
    case configuration = 0

    /// Structured logging subsystem initialization.
    case logging = 1

    /// Dependency injection container and assembly.
    case dependencyInjection = 2

    /// Application state and lifecycle state.
    case applicationState = 3

    /// Window manager, menu bar, overlay.
    case windowSystem = 4

    /// Final initialization. Services that depend on all prior phases.
    case ready = 5

    // MARK: - Properties

    /// A human-readable label for diagnostics and logging.
    public var label: String {
        switch self {
        case .configuration: "Configuration"
        case .logging: "Logging"
        case .dependencyInjection: "Dependency Injection"
        case .applicationState: "App State"
        case .windowSystem: "Window System"
        case .ready: "Application Ready"
        }
    }

    // MARK: - Comparable

    public static func < (lhs: StartupPhase, rhs: StartupPhase) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}
