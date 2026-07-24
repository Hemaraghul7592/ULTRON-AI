import Foundation

/// Compile-time constants that define ULTRON's behavior boundaries.
///
/// Unlike `Configuration` (which reads from the runtime environment),
/// `Constants` values are hardcoded and should rarely change. They define
/// the fixed parameters of the application — sizes, limits, identifiers.
///
/// If a value needs to be configurable per-user or per-environment,
/// it belongs in `Configuration` or `UserDefaults`, not here.
public enum Constants {

    // MARK: - App Identity

    /// The canonical bundle identifier for ULTRON.
    public static let bundleIdentifier = "ai.ultron.app"

    /// The application display name shown in the menu bar and About panel.
    public static let displayName = "ULTRON"

    // MARK: - Window Defaults

    /// Default width for the main window in points.
    public static let mainWindowDefaultWidth: CGFloat = 900

    /// Default height for the main window in points.
    public static let mainWindowDefaultHeight: CGFloat = 650

    /// Minimum width for the main window in points.
    public static let mainWindowMinimumWidth: CGFloat = 600

    /// Minimum height for the main window in points.
    public static let mainWindowMinimumHeight: CGFloat = 400

    /// Default width for the overlay window in points.
    public static let overlayWindowDefaultWidth: CGFloat = 680

    /// Default height for the overlay window in points.
    public static let overlayWindowDefaultHeight: CGFloat = 420

    /// Default width for the settings window in points.
    public static let settingsWindowDefaultWidth: CGFloat = 780

    /// Default height for the settings window in points.
    public static let settingsWindowDefaultHeight: CGFloat = 560

    // MARK: - Timing

    /// Duration in seconds for standard UI animations.
    public static let defaultAnimationDuration: TimeInterval = 0.25

    /// Duration in seconds for overlay appearance animation.
    public static let overlayAppearDuration: TimeInterval = 0.2

    /// Duration in seconds for overlay dismissal animation.
    public static let overlayDismissDuration: TimeInterval = 0.15

    // MARK: - Limits

    /// Maximum length of a user input string before truncation.
    public static let maxUserInputLength = 10000

    /// Maximum number of startup retries before giving up.
    public static let maxStartupRetries = 3

    // MARK: - URLs

    /// The project homepage.
    public static let projectURL = "https://ultron.ai"

    /// The privacy policy URL.
    public static let privacyPolicyURL = "https://ultron.ai/privacy"

    /// The documentation URL.
    public static let documentationURL = "https://docs.ultron.ai"
}
