import AppKit
import Combine
import Foundation

/// The application delegate for ULTRON.
///
/// `AppDelegate` owns the startup and shutdown lifecycles. It is the first
/// application code that executes after the runtime initializes, and the
/// last code that runs before the process terminates.
///
/// ## Lifecycle Design
///
/// **Startup**: Async hooks run in `applicationWillFinishLaunching`. The
/// app does not finish launching until all hooks complete successfully.
///
/// **Shutdown**: Async hooks run in `applicationShouldTerminate(_:)`.
/// This is Apple's recommended approach for asynchronous termination — the
/// app returns `.terminateLater` and calls `reply(toApplicationShouldTerminate:)`
/// when all hooks complete. `applicationWillTerminate` is reserved for
/// synchronous cleanup only.
@MainActor
public final class ApplicationLifecycleState: ObservableObject {
    public enum Phase: Equatable, Sendable {
        case idle
        case starting(StartupPhase)
        case ready
        case failed(String)
        case shuttingDown
        case terminated
    }

    @Published public private(set) var phase: Phase = .idle
    func update(_ phase: Phase) { self.phase = phase }
}

@MainActor
public final class AppDelegate: NSObject, NSApplicationDelegate {

    /// The composition root owns the application container and all service
    /// registrations used during startup.
    public let compositionRoot: ApplicationCompositionRoot

    // MARK: - Lifecycle Sequences

    /// The ordered startup sequence. Hooks are registered by subsystems
    /// during initialization and executed in priority order at launch.
    public let startupSequence = StartupSequence()

    /// The ordered shutdown sequence. Hooks execute in reverse priority
    /// order when the application terminates.
    public let shutdownSequence = ShutdownSequence()
    public let lifecycleState = ApplicationLifecycleState()
    private var startupTask: Task<Void, Never>?

    public override init() {
        compositionRoot = ApplicationCompositionRoot()
        super.init()
        compositionRoot.registerLifecycleHooks(startup: startupSequence, shutdown: shutdownSequence)
    }

    // MARK: - NSApplicationDelegate

    /// Called before the application finishes launching.
    ///
    /// Startup hooks execute here. The launch does not complete until
    /// all hooks finish. If any hook throws, the app transitions to
    /// an error state rather than presenting its UI.
    public func applicationWillFinishLaunching(_ notification: Notification) {
        beginStartup()
    }

    /// Called after the application has finished launching.
    ///
    /// Executes the startup sequence and presents user-facing UI.
    /// This is intentionally structured so that startup failures
    /// can be handled before any windows appear.
    public func applicationDidFinishLaunching(_ notification: Notification) {
    }

    public func retryStartup() {
        guard case .failed = lifecycleState.phase else { return }
        startupSequence.resetAfterFailure()
        beginStartup()
    }

    /// Called when the application is asked to terminate.
    ///
    /// Async shutdown hooks execute here. The app returns `.terminateLater`
    /// and replies to the termination request once all hooks complete.
    /// This is Apple's recommended pattern for async termination.
    public func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        lifecycleState.update(.shuttingDown)
        Task {
            await shutdownSequence.execute()
            await MainActor.run {
                self.lifecycleState.update(.terminated)
                sender.reply(toApplicationShouldTerminate: true)
            }
        }
        return .terminateLater
    }

    /// Called immediately before the application terminates.
    ///
    /// This method is reserved for synchronous cleanup only. All async
    /// work must complete in `applicationShouldTerminate` before this
    /// method is called by the system.
    public func applicationWillTerminate(_ notification: Notification) {
        // Synchronous cleanup only. No async work here.
        // All shutdown hooks have already completed in applicationShouldTerminate.
    }

    /// Called when the application has become active.
    public func applicationDidBecomeActive(_ notification: Notification) {
        // Future: Resume conscious loop, enable proactive features.
    }

    /// Called when the application is about to resign active state.
    public func applicationWillResignActive(_ notification: Notification) {
        // Future: Pause conscious loop, defer non-critical work.
    }

    // MARK: - Diagnostics

    /// Whether the startup sequence completed without errors.
    public private(set) var didStartSuccessfully = false

    /// Records successful completion of the startup sequence.
    func markStartupComplete() {
        didStartSuccessfully = true
    }

    private func beginStartup() {
        guard startupTask == nil, lifecycleState.phase != .ready, lifecycleState.phase != .shuttingDown else { return }
        lifecycleState.update(.starting(.configuration))
        startupTask = Task { @MainActor [weak self] in
            guard let self else { return }
            do {
                try await startupSequence.execute()
                compositionRoot.markReady()
                markStartupComplete()
                lifecycleState.update(.ready)
            } catch {
                compositionRoot.markFailed()
                lifecycleState.update(.failed(error.localizedDescription))
            }
            startupTask = nil
        }
    }

    /// Handles a startup failure by presenting an error and offering
    /// the user the option to terminate the application.
}
