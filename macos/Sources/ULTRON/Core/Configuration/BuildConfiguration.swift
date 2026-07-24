/// Identifies the current build configuration at runtime.
///
/// ULTRON compiles with one of four configurations selected at build time
/// via the `SWIFT_ACTIVE_COMPILATION_CONDITIONS` compiler flag. This enum
/// enables runtime code paths to vary behavior based on configuration
/// without scattering `#if` checks throughout the codebase.
///
/// ```swift
/// if BuildConfiguration.current >= .release {
///     // Only log detailed performance metrics in release/production builds
/// }
/// ```
public enum BuildConfiguration: Int, Comparable, Sendable {
    /// Active development. All debug features enabled. Assertions active.
    case development = 0

    /// Internal testing. Additional instrumentation beyond development.
    case debug = 1

    /// Beta distribution. Optimized but retains debug symbols.
    case release = 2

    /// End-user distribution. Maximum optimization, minimum overhead.
    case production = 3

    // MARK: - Current

    /// The build configuration of the running binary.
    ///
    /// Determined at compile time by the `SWIFT_ACTIVE_COMPILATION_CONDITIONS`
    /// flag set in the active `.xcconfig` file.
    public static var current: BuildConfiguration {
        #if PRODUCTION
            return .production
        #elseif RELEASE
            return .release
        #elseif DEBUG
            return .debug
        #else
            return .development
        #endif
    }

    // MARK: - Properties

    /// Whether this configuration enables debug-level logging and assertions.
    public var isDebugEnabled: Bool {
        self <= .debug
    }

    /// Whether this configuration is optimized for end-user distribution.
    public var isOptimized: Bool {
        self >= .release
    }

    /// A human-readable label for display in diagnostic output.
    public var label: String {
        switch self {
        case .development: "Development"
        case .debug: "Debug"
        case .release: "Release"
        case .production: "Production"
        }
    }

    public static func < (lhs: BuildConfiguration, rhs: BuildConfiguration) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}
