import Foundation

/// Centralized access to compile-time and runtime configuration values.
///
/// `Configuration` is the single source of truth for all tunable parameters
/// in ULTRON. It reads from build flags, environment variables, and
/// (in future milestones) user settings and remote feature flags.
///
/// All configuration access should flow through this type rather than
/// reading `UserDefaults`, `ProcessInfo`, or compile flags directly.
///
/// ## Thread Safety
///
/// `Configuration` is a value type with only static properties derived from
/// compile-time constants and `ProcessInfo`. It is safe to access from any
/// concurrency domain.
public struct Configuration: Sendable {

    // MARK: - App Identity

    /// The application bundle identifier.
    public static let bundleIdentifier: String = {
        Bundle.main.bundleIdentifier ?? "ai.ultron.app"
    }()

    /// The human-readable application name.
    public static let appName: String = {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleName") as? String ?? "ULTRON"
    }()

    /// The semantic version of the running build.
    public static let appVersion: String = {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0.0"
    }()

    /// The build number from the bundle.
    public static let buildNumber: String = {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "1"
    }()

    // MARK: - Build

    /// The active build configuration.
    public static let buildConfiguration: BuildConfiguration = .current

    /// Whether this is a development or debug build.
    public static let isDebugBuild: Bool = BuildConfiguration.current.isDebugEnabled

    // MARK: - Environment

    /// Whether the process was launched by Xcode (running from the debugger).
    public static let isRunningInXcode: Bool = {
        ProcessInfo.processInfo.environment["__XCODE_BUILT_PRODUCTS_DIR_PATHS"] != nil
    }()

    /// Whether the process is running in a test environment.
    /// Detects both XCTest and Swift Testing.
    public static let isTesting: Bool = {
        NSClassFromString("XCTestCase") != nil
            || ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil
            || CommandLine.arguments.contains { $0.hasSuffix(".xctest") || $0.contains("swift-testing") }
    }()

    // MARK: - Runtime

    /// The current macOS version as a string (e.g., "15.2").
    public static let macOSVersion: String = {
        let version = ProcessInfo.processInfo.operatingSystemVersion
        return "\(version.majorVersion).\(version.minorVersion).\(version.patchVersion)"
    }()

    /// A unique identifier for this launch session.
    ///
    /// Regenerated on every app launch. Used for correlating log entries
    /// and distinguishing between different runs in diagnostic output.
    public static let launchSessionID: String = {
        UUID().uuidString
    }()
}
