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
    /// In this milestone, a single window with no content is provided
    /// to satisfy the `App` protocol requirement. The actual window
    /// architecture (main, overlay, settings) will be managed by
    /// `WindowManager` in a subsequent milestone.
    var body: some Scene {
        WindowGroup {
            ContentPlaceholderView()
                .frame(minWidth: 400, minHeight: 300)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        .defaultSize(width: 900, height: 650)
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

// MARK: - Content Placeholder

/// A minimal view that serves as the root content until the window
/// architecture is implemented in a future milestone.
///
/// This view will be replaced by the full window management system
/// when the Window Manager milestone is reached.
private struct ContentPlaceholderView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)

            Text("ULTRON")
                .font(.largeTitle)
                .fontWeight(.medium)

            Text("Personal AI Operating Companion")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
