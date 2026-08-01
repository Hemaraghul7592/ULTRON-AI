/// A capability that a service provider can fulfill.
///
/// Providers declare which capabilities they support. The orchestrator
/// uses capability matching to route requests to the correct provider.
/// New capabilities can be added without modifying existing providers.
public struct ServiceCapability: Sendable, Hashable {
    public let rawValue: String

    public init(_ rawValue: String) {
        self.rawValue = rawValue
    }

    // MARK: - Common Capabilities

    public static let chat = ServiceCapability("chat")
    public static let embedding = ServiceCapability("embedding")
    public static let vision = ServiceCapability("vision")
    public static let search = ServiceCapability("search")
    public static let weather = ServiceCapability("weather")
    public static let ocr = ServiceCapability("ocr")
    public static let maps = ServiceCapability("maps")
    public static let voice = ServiceCapability("voice")
    public static let routing = ServiceCapability("routing")
}
