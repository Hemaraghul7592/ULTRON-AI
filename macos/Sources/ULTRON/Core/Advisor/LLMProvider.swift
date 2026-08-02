/// Protocol for LLM providers used by the AI Advisor.
public protocol LLMProvider: Sendable, Identifiable {
    var providerName: String { get }
    var providerID: String { get }
    var isAvailable: Bool { get async }

    /// Sends a prompt and returns the generated text.
    func generate(prompt: String, systemPrompt: String) async throws -> String

    /// Health check for availability.
    func healthCheck() async -> Bool
}

public extension LLMProvider {
    var providerID: String { providerName }
}

public typealias LLMResponseStream = AsyncThrowingStream<String, Error>

public extension LLMProvider {
    func generateStream(prompt: String, systemPrompt: String) -> LLMResponseStream {
        LLMResponseStream { continuation in
            let task = Task {
                do {
                    try Task.checkCancellation()
                    let response = try await generate(prompt: prompt, systemPrompt: systemPrompt)
                    try Task.checkCancellation()
                    continuation.yield(response)
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }
}

/// Default LLM error types.
public enum LLMError: Error {
    case unavailable(String), timeout, rateLimited
}
