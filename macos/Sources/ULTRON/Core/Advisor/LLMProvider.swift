/// Protocol for LLM providers used by the AI Advisor.
public protocol LLMProvider: Sendable, Identifiable {
    var providerName: String { get }
    var isAvailable: Bool { get async }

    /// Sends a prompt and returns the generated text.
    func generate(prompt: String, systemPrompt: String) async throws -> String

    /// Health check for availability.
    func healthCheck() async -> Bool
}

/// Default LLM error types.
public enum LLMError: Error {
    case unavailable(String), timeout, rateLimited
}
