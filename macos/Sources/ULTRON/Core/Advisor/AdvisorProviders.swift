import Foundation

/// OpenRouter LLM adapter — routes to multiple cloud LLM backends.
public actor OpenRouterAdapter: LLMProvider {
    public let id = "openrouter"
    public let providerName = "OpenRouter"

    private let apiKey: String
    private let session: URLSession
    private var isAvailableFlag = true

    public init(apiKey: String? = nil) {
        self.apiKey = apiKey ?? APIConfiguration.shared.openRouterKey
        session = URLSession(configuration: .ephemeral)
    }

    public var isAvailable: Bool { isAvailableFlag }

    public func generate(prompt: String, systemPrompt: String) async throws -> String {
        try Task.checkCancellation()
        guard !apiKey.isEmpty else { throw LLMError.unavailable("OpenRouter key missing") }
        let url = URL(string: "https://openrouter.ai/api/v1/chat/completions")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "model": "openai/gpt-4o-mini",
            "messages": [["role": "system", "content": systemPrompt], ["role": "user", "content": prompt]],
            "max_tokens": 1024,
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: req)
        try Task.checkCancellation()
        guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw LLMError.unavailable("OpenRouter returned error") }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let choices = json["choices"] as? [[String: Any]],
              let message = choices.first?["message"] as? [String: Any],
              let content = message["content"] as? String
        else { throw LLMError.unavailable("OpenRouter parse error") }
        return content
    }

    public func healthCheck() async -> Bool {
        guard !apiKey.isEmpty else { isAvailableFlag = false; return false }
        do {
            let _ = try await generate(prompt: "health", systemPrompt: "Reply OK")
            isAvailableFlag = true; return true
        } catch { isAvailableFlag = false; return false }
    }
}

/// Local Ollama LLM adapter — runs models on-device.
public actor OllamaAdapter: LLMProvider {
    public let id = "ollama"
    public let providerName = "Ollama"

    private let endpoint: String
    private let session: URLSession
    private var isAvailableFlag = true

    public init(endpoint: String? = nil) {
        self.endpoint = endpoint ?? APIConfiguration.shared.ollamaEndpoint
        session = URLSession(configuration: .ephemeral)
    }

    public var isAvailable: Bool { isAvailableFlag }

    public func generate(prompt: String, systemPrompt: String) async throws -> String {
        try Task.checkCancellation()
        let url = URL(string: "\(endpoint)/api/generate")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["model": "llama3.2", "prompt": "\(systemPrompt)\n\n\(prompt)", "stream": false]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: req)
        try Task.checkCancellation()
        guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw LLMError.unavailable("Ollama unavailable") }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let content = json["response"] as? String
        else { throw LLMError.unavailable("Ollama parse error") }
        return content
    }

    public func healthCheck() async -> Bool {
        do {
            let _ = try await generate(prompt: "health", systemPrompt: "Reply OK")
            isAvailableFlag = true; return true
        } catch { isAvailableFlag = false; return false }
    }
}

/// Mock LLM provider for testing.
public actor MockLLMProvider: LLMProvider {
    public let id = "mock"
    public let providerID = UUID().uuidString
    public let providerName = "Mock"
    public var response: String
    private var availableFlag = true

    public init(response: String = "Mock AI response.") { self.response = response }
    public var isAvailable: Bool { availableFlag }
    public func setAvailable(_ value: Bool) { availableFlag = value }
    public func generate(prompt: String, systemPrompt: String) async throws -> String { response }
    public func healthCheck() async -> Bool { availableFlag }
}
