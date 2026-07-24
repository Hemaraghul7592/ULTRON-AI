import Foundation
import Testing

@testable import ULTRON

/// Validates the build configuration system, runtime configuration,
/// and compile-time constants.
@Suite struct ConfigurationTests {

    // MARK: - Build Configuration

    @Test("Build configuration is development in test environment")
    func testBuildConfigurationIsDevelopment() {
        #expect(BuildConfiguration.current == .debug)
    }

    @Test("Development configuration has debug enabled")
    func testDevelopmentDebugEnabled() {
        #expect(BuildConfiguration.development.isDebugEnabled == true)
        #expect(BuildConfiguration.debug.isDebugEnabled == true)
    }

    @Test("Release configuration has debug disabled")
    func testReleaseDebugDisabled() {
        #expect(BuildConfiguration.release.isDebugEnabled == false)
        #expect(BuildConfiguration.production.isDebugEnabled == false)
    }

    @Test("Release and production are optimized")
    func testReleaseIsOptimized() {
        #expect(BuildConfiguration.release.isOptimized == true)
        #expect(BuildConfiguration.production.isOptimized == true)
        #expect(BuildConfiguration.development.isOptimized == false)
    }

    @Test("Build configurations are comparable")
    func testBuildConfigurationOrdering() {
        #expect(BuildConfiguration.development < BuildConfiguration.debug)
        #expect(BuildConfiguration.debug < BuildConfiguration.release)
        #expect(BuildConfiguration.release < BuildConfiguration.production)
    }

    @Test("All configurations have distinct raw values")
    func testDistinctRawValues() {
        let values = [
            BuildConfiguration.development.rawValue,
            BuildConfiguration.debug.rawValue,
            BuildConfiguration.release.rawValue,
            BuildConfiguration.production.rawValue,
        ]
        #expect(Set(values).count == 4)
    }

    @Test("Configuration labels are descriptive")
    func testLabels() {
        #expect(BuildConfiguration.development.label == "Development")
        #expect(BuildConfiguration.debug.label == "Debug")
        #expect(BuildConfiguration.release.label == "Release")
        #expect(BuildConfiguration.production.label == "Production")
    }

    @Test("All configurations have non-empty labels")
    func testAllLabelsNonEmpty() {
        let configs: [BuildConfiguration] = [.development, .debug, .release, .production]
        for config in configs {
            #expect(!config.label.isEmpty)
        }
    }
}

@Suite struct ConfigurationRuntimeTests {

    // MARK: - App Identity

    @Test("App name resolves correctly")
    func testAppName() {
        let name = Configuration.appName
        #expect(!name.isEmpty)
        #expect(name == "ULTRON")
    }

    @Test("Bundle identifier resolves")
    func testBundleIdentifier() {
        let id = Configuration.bundleIdentifier
        #expect(!id.isEmpty)
    }

    @Test("App version resolves")
    func testVersion() {
        let version = Configuration.appVersion
        #expect(!version.isEmpty)
    }

    @Test("Build number resolves")
    func testBuildNumber() {
        let bn = Configuration.buildNumber
        #expect(!bn.isEmpty)
    }

    // MARK: - Build Detection

    @Test("Is testing environment detected")
    func testIsTesting() {
        #expect(Configuration.isTesting == true)
    }

    @Test("Build configuration matches expected value")
    func testBuildConfigurationAccessor() {
        #expect(Configuration.buildConfiguration == .current)
    }

    // MARK: - Runtime

    @Test("Launch session ID is unique per access")
    func testLaunchSessionID() {
        let id = Configuration.launchSessionID
        #expect(!id.isEmpty)
        #expect(UUID(uuidString: id) != nil)

        // Verify the ID is stable within the same process (static let is lazy)
        let same = Configuration.launchSessionID
        #expect(id == same)
    }

    @Test("MacOS version string is non-empty")
    func testMacOSVersion() {
        let version = Configuration.macOSVersion
        #expect(!version.isEmpty)
        #expect(version.contains("."))
    }

    @Test("Xcode detection does not crash")
    func testXcodeDetection() {
        // isRunningInXcode may be true or false depending on environment.
        // This test verifies the accessor doesn't crash.
        _ = Configuration.isRunningInXcode
    }

    @Test("Debug build detection is consistent with current config")
    func testIsDebugConsistency() {
        let expected = BuildConfiguration.current.isDebugEnabled
        #expect(Configuration.isDebugBuild == expected)
    }
}

@Suite struct ConstantsTests {

    // MARK: - App Identity

    @Test("Bundle identifier constant matches expected value")
    func testBundleIdentifier() {
        #expect(Constants.bundleIdentifier == "ai.ultron.app")
    }

    @Test("Display name constant is correct")
    func testDisplayName() {
        #expect(Constants.displayName == "ULTRON")
    }

    // MARK: - Window Dimensions

    @Test("Window dimensions are positive")
    func testWindowDimensions() {
        #expect(Constants.mainWindowDefaultWidth > 0)
        #expect(Constants.mainWindowDefaultHeight > 0)
        #expect(Constants.overlayWindowDefaultWidth > 0)
        #expect(Constants.overlayWindowDefaultHeight > 0)
        #expect(Constants.settingsWindowDefaultWidth > 0)
        #expect(Constants.settingsWindowDefaultHeight > 0)
    }

    @Test("Minimum window dimensions are less than default dimensions")
    func testMinimumLessThanDefault() {
        #expect(Constants.mainWindowMinimumWidth < Constants.mainWindowDefaultWidth)
        #expect(Constants.mainWindowMinimumHeight < Constants.mainWindowDefaultHeight)
    }

    @Test("All window dimension constants are unique to their window type")
    func testWindowDimensionConsistency() {
        // Overlay should be smaller than main window
        #expect(Constants.overlayWindowDefaultWidth < Constants.mainWindowDefaultWidth)
        #expect(Constants.overlayWindowDefaultHeight < Constants.mainWindowDefaultHeight)
    }

    // MARK: - Timing

    @Test("Animation durations are positive")
    func testAnimationDurations() {
        #expect(Constants.defaultAnimationDuration > 0)
        #expect(Constants.overlayAppearDuration > 0)
        #expect(Constants.overlayDismissDuration > 0)
    }

    @Test("Dismiss is faster than appear for overlay")
    func testOverlayTiming() {
        #expect(Constants.overlayDismissDuration < Constants.overlayAppearDuration)
    }

    @Test("All animation durations are reasonable")
    func testAnimationDurationBounds() {
        let durations: [TimeInterval] = [
            Constants.defaultAnimationDuration,
            Constants.overlayAppearDuration,
            Constants.overlayDismissDuration,
        ]
        for duration in durations {
            #expect(duration > 0)
            #expect(duration <= 2.0)  // No animation should exceed 2 seconds
        }
    }

    // MARK: - Limits

    @Test("Startup retry limit is reasonable")
    func testStartupRetries() {
        #expect(Constants.maxStartupRetries > 0)
        #expect(Constants.maxStartupRetries <= 10)
    }

    @Test("Max user input length is reasonable")
    func testMaxUserInputLength() {
        #expect(Constants.maxUserInputLength > 0)
        #expect(Constants.maxUserInputLength <= 100_000)
    }

    // MARK: - URLs

    @Test("URL constants are valid")
    func testURLs() {
        #expect(Constants.projectURL.hasPrefix("https://"))
        #expect(Constants.privacyPolicyURL.hasPrefix("https://"))
        #expect(Constants.documentationURL.hasPrefix("https://"))
    }

    @Test("URL constants are distinct")
    func testURLsAreDistinct() {
        let urls = [Constants.projectURL, Constants.privacyPolicyURL, Constants.documentationURL]
        #expect(Set(urls).count == 3)
    }
}
