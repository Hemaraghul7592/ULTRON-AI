/// Orchestrates the ordered startup of all registered lifecycle hooks.
///
/// `StartupSequence` executes hooks in ascending phase order, then by
/// ascending priority within each phase. Phases are defined by the
/// `StartupPhase` enum — new phases are added by extending the enum,
/// requiring zero changes to this type.
///
/// ## Execution Order
///
/// ```
/// configuration → logging → dependencyInjection
///     → applicationState → windowSystem → ready
/// ```
///
/// Within each phase, hooks with lower `priority` values execute first.
/// Hooks with equal priority execute in registration order.
///
/// This type is confined to the main actor.
@MainActor
public final class StartupSequence {

    // MARK: - State

    /// The list of registered hooks, sorted by (phase, priority, registration order).
    private var hooks: [any LifecycleHook] = []

    /// The current phase during execution, for diagnostic purposes.
    public private(set) var currentPhase: StartupPhase = .configuration

    // MARK: - Registration

    /// Registers a lifecycle hook for execution during startup.
    ///
    /// Hooks are sorted by phase first, then by priority within each phase.
    /// Multiple hooks with the same phase and priority execute in
    /// registration order.
    ///
    /// - Parameter hook: The hook to register.
    public func register(_ hook: any LifecycleHook) {
        hooks.append(hook)
        sortHooks()
    }

    /// Registers multiple hooks at once. Equivalent to calling
    /// `register(_:)` for each hook, then sorting once.
    public func register(_ newHooks: [any LifecycleHook]) {
        hooks.append(contentsOf: newHooks)
        sortHooks()
    }

    /// Sorts hooks by (phase ascending, priority ascending).
    /// Registration order is preserved as a stable tiebreaker by
    /// using the existing array order (append order).
    private func sortHooks() {
        hooks.sort { a, b in
            if a.phase != b.phase {
                return a.phase < b.phase
            }
            return a.priority < b.priority
        }
    }

    // MARK: - Execution

    /// Executes all registered hooks in order.
    ///
    /// If any hook throws, the sequence stops immediately — subsequent
    /// hooks and phases are not executed. The caller is responsible for
    /// handling the failure.
    ///
    /// - Throws: The error from the first hook that fails.
    public func execute() async throws {
        for hook in hooks {
            currentPhase = hook.phase
            try await hook.onStartup()
        }
    }

    // MARK: - Diagnostics

    /// The number of registered hooks.
    public var count: Int { hooks.count }

    /// Whether any hooks are registered.
    public var isEmpty: Bool { hooks.isEmpty }

    /// Returns hooks grouped by their phase for diagnostic display.
    public func hooksByPhase() -> [(phase: StartupPhase, label: String, count: Int)] {
        var result: [(StartupPhase, String, Int)] = []
        for phase in StartupPhase.allCases {
            let phaseHooks = hooks.filter { $0.phase == phase }
            if !phaseHooks.isEmpty {
                result.append((phase, phase.label, phaseHooks.count))
            }
        }
        return result
    }
}
