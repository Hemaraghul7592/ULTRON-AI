/// Orchestrates the ordered shutdown of all registered lifecycle hooks.
///
/// `ShutdownSequence` executes hooks in descending phase order (reverse
/// of startup), then by descending priority within each phase. This
/// ensures that dependencies started last are stopped first.
///
/// ## Execution Order
///
/// ```
/// ready → windowSystem → applicationState
///     → dependencyInjection → logging → configuration
/// ```
///
/// Within each phase, hooks with higher `priority` values execute first.
/// Every hook is guaranteed to execute — shutdown is fire-and-forget.
///
/// This type is confined to the main actor.
@MainActor
public final class ShutdownSequence {

    // MARK: - State

    /// The list of registered hooks, sorted by descending (phase, priority).
    private var hooks: [any LifecycleHook] = []

    // MARK: - Registration

    /// Registers a lifecycle hook for execution during shutdown.
    ///
    /// Hooks are sorted by descending phase (reverse startup order),
    /// then by descending priority within each phase. Multiple hooks
    /// with the same phase and priority execute in registration order.
    ///
    /// - Parameter hook: The hook to register.
    public func register(_ hook: any LifecycleHook) {
        hooks.append(hook)
        sortHooks()
    }

    /// Registers multiple hooks at once.
    public func register(_ newHooks: [any LifecycleHook]) {
        hooks.append(contentsOf: newHooks)
        sortHooks()
    }

    /// Sorts hooks by (phase descending, priority descending).
    private func sortHooks() {
        hooks.sort { a, b in
            if a.phase != b.phase {
                return a.phase > b.phase
            }
            return a.priority > b.priority
        }
    }

    // MARK: - Execution

    /// Executes all registered hooks in reverse startup order.
    ///
    /// Every hook runs regardless of whether others encountered issues.
    /// The shutdown sequence is fire-and-forget — the application will
    /// terminate after this method returns.
    public func execute() async {
        for hook in hooks {
            await hook.onShutdown()
        }
    }

    // MARK: - Diagnostics

    /// The number of registered hooks.
    public var count: Int { hooks.count }

    /// Whether any hooks are registered.
    public var isEmpty: Bool { hooks.isEmpty }
}
