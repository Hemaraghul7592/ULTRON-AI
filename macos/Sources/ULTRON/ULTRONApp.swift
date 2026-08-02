import SwiftUI

/// The entry point for the ULTRON macOS application.
///
/// `ULTRONApp` conforms to the SwiftUI `App` protocol. It uses
/// `NSApplicationDelegateAdaptor` to bridge the SwiftUI app lifecycle
/// with the traditional `NSApplicationDelegate` callbacks, which provide
/// finer-grained control over the application lifecycle.
///
/// ## Architecture
///
/// The app initializes in this order:
/// 1. `AppDelegate` is created (via `@NSApplicationDelegateAdaptor`)
/// 2. `applicationWillFinishLaunching` — startup sequence begins
/// 3. `applicationDidFinishLaunching` — UI presentation, service start
/// 4. Scene phase changes (active ↔ inactive ↔ background)
/// 5. `applicationWillTerminate` — shutdown sequence executes
///
/// ## Scene Management
///
/// The `WindowGroup` with `windowStyle(.hiddenTitleBar)` provides a
/// modern appearance. Individual windows (overlay, settings) will be
/// managed by a `WindowManager` in a future milestone rather than
/// declared declaratively here.
@main
struct ULTRONApp: App {
    // MARK: - App Delegate

    /// Bridges NSApplicationDelegate into the SwiftUI app lifecycle.
    @NSApplicationDelegateAdaptor(AppDelegate.self)
    var appDelegate

    // MARK: - Scene Phase

    /// Tracks the current scene phase for lifecycle state transitions.
    @Environment(\.scenePhase)
    private var scenePhase

    // MARK: - Body

    /// The root scene of the application.
    ///
    /// The application delegate constructs the composition root before the
    /// first scene is presented. The scene therefore starts only after the
    /// same service graph used by lifecycle startup has been assembled.
    var body: some Scene {
        WindowGroup {
            if case .ready = appDelegate.lifecycleState.phase {
                AppShell(compositionRoot: appDelegate.compositionRoot)
                    .frame(minWidth: 900, minHeight: 650)
            } else {
                StartupGateView(state: appDelegate.lifecycleState) {
                    appDelegate.retryStartup()
                }
                .frame(minWidth: 520, minHeight: 360)
            }
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        .defaultSize(width: 1200, height: 800)
        .onChange(of: scenePhase) { _, newPhase in
            handleScenePhaseChange(newPhase)
        }
    }

    // MARK: - Lifecycle Handling

    /// Responds to scene phase transitions.
    ///
    /// Scene phase is SwiftUI's mechanism for tracking whether the
    /// application's windows are active, inactive, or in the background.
    /// Future milestones will use this to pause/resume the conscious loop.
    private func handleScenePhaseChange(_ phase: ScenePhase) {
        switch phase {
        case .active:
            break  // Future: resume conscious loop
        case .inactive:
            break  // Future: transition to inactive state
        case .background:
            break  // Future: pause non-essential work
        @unknown default:
            break
        }
    }
}

private struct StartupGateView: View {
    @ObservedObject var state: ApplicationLifecycleState
    let retry: () -> Void

    var body: some View {
        VStack(spacing: 18) {
            Image(systemName: "bolt.horizontal.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(.blue)
            Text("ULTRON")
                .font(.largeTitle.weight(.bold))
            switch state.phase {
            case .failed(let message):
                Text("ULTRON could not start")
                    .font(.headline)
                Text(message)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                Button("Retry Startup", action: retry)
                    .buttonStyle(.borderedProminent)
            case .shuttingDown:
                ProgressView("Shutting down...")
            case .terminated:
                Text("ULTRON has stopped.")
            default:
                ProgressView("Starting ULTRON...")
            }
        }
        .padding(36)
        .accessibilityIdentifier("startup.gate")
    }
}
