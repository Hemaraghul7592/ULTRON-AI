/// A category of external service that ULTRON integrates with.
///
/// Categories group providers that serve the same purpose (e.g., all AI
/// models belong to `.ai`). The orchestrator uses categories to organize
/// provider registries and to produce meaningful diagnostic output.
public enum ServiceCategory: String, Sendable, CaseIterable {
    case ai = "ai"
    case search = "search"
    case weather = "weather"
    case maps = "maps"
    case ocr = "ocr"
    case speech = "speech"
    case email = "email"
    case calendar = "calendar"
    case storage = "storage"
    case custom = "custom"
}
