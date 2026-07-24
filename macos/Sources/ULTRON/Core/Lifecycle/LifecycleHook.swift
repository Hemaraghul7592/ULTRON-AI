/// A hook that participates in ULTRON's startup and shutdown sequences.
///
/// Types conforming to `LifecycleHook` register themselves with the
/// `StartupSequence` or `ShutdownSequence` to execute work at a specific
/// point during the application lifecycle.
///
/// ## Phase and Priority
///
/// Each hook declares a `phase` that determines which initialization stage
/// it belongs to. Hooks within the same phase are ordered by `priority`
/// (lower values execute first on startup, last on shutdown).
///
/// ## Example
/// ```swift
/// struct DatabaseHook: LifecycleHook {
///     let phase: StartupPhase = .dependencyInjection
///     let priority: Int = 10
///     let label = "Database"
///
///     func onStartup() async throws {
///         try await Database.initialize()
///     }
///
///     func onShutdown() async {
///         await Database.close()
///     }
/// }
/// ```
///
/// ## Concurrency
///
/// Hooks are registered and executed on the `@MainActor` via
/// `StartupSequence` and `ShutdownSequence`. The protocol does not
/// require `Sendable` conformance because hooks never leave the
/// main actor's isolation domain.
public protocol LifecycleHook: Identifiable {

    /// The startup phase this hook belongs to.
    /// Phases execute in `StartupPhase.allCases` order.
    var phase: StartupPhase { get }

    /// The execution priority within the hook's phase.
    /// Lower values execute first on startup, last on shutdown.
    /// The default value is 0 (earliest in phase).
    var priority: Int { get }

    /// A human-readable label for logging and diagnostics.
    var label: String { get }

    /// Called during application startup.
    /// Throwing prevents the app from completing its launch sequence.
    func onStartup() async throws

    /// Called during application shutdown.
    /// This method should not throw; failures are logged but do not
    /// prevent termination.
    func onShutdown() async
}

public extension LifecycleHook {
    /// Default priority: executes at the beginning of its phase.
    var priority: Int { 0 }

    /// Hook identity derived from its label.
    var id: String { label }
}
