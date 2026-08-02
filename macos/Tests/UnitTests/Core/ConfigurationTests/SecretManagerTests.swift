import Testing

@testable import ULTRON

@Suite struct SecretManagerTests {
    @Test("Environment values override local and example values")
    func environmentPrecedence() throws {
        let manager = SecretManager(
            environment: ["FINNHUB_API_KEY": "environment-key"],
            keychainLookup: { _ in "keychain-key" },
            localValues: ["FINNHUB_API_KEY": "local-key"],
            exampleValues: ["FINNHUB_API_KEY": "YOUR_FINNHUB_API_KEY"]
        )
        #expect(manager.finnhubKey == "environment-key")
    }

    @Test("Keychain values override local values")
    func keychainPrecedence() {
        let manager = SecretManager(
            environment: [:],
            keychainLookup: { _ in "keychain-key" },
            localValues: ["FINNHUB_API_KEY": "local-key"],
            exampleValues: [:]
        )
        #expect(manager.finnhubKey == "keychain-key")
    }

    @Test("Placeholder values are not treated as secrets")
    func placeholders() throws {
        let manager = SecretManager(
            environment: ["FINNHUB_API_KEY": "YOUR_FINNHUB_API_KEY"],
            keychainLookup: { _ in nil },
            localValues: [:],
            exampleValues: ["FINNHUB_API_KEY": "PLACEHOLDER"]
        )
        #expect(manager.finnhubKey.isEmpty)
        do {
            try manager.validate(required: [.finnhubAPIKey])
            Issue.record("Expected missing secret validation failure")
        } catch let error as SecretManagerError {
            #expect(error == .missingRequiredSecret(.finnhubAPIKey))
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("Invalid local configuration is reported")
    func invalidLocalConfiguration() {
        let manager = SecretManager(environment: [:], keychainLookup: { _ in nil }, localValues: [:], exampleValues: [:], configurationError: .invalidLocalConfiguration)
        do {
            try manager.validate(required: [])
            Issue.record("Expected invalid local configuration failure")
        } catch let error as SecretManagerError {
            #expect(error == .invalidLocalConfiguration)
        } catch {
            Issue.record("Unexpected error: \(error)")
        }
    }

    @Test("Required secret validation succeeds for configured values")
    func requiredSecretValidation() throws {
        let manager = SecretManager(environment: ["FINNHUB_API_KEY": "configured"], keychainLookup: { _ in nil }, localValues: [:], exampleValues: [:])
        try manager.validate(required: [.finnhubAPIKey])
    }

    @Test("Redaction never returns a secret value")
    func redaction() {
        #expect(SecretManager.redacted("sensitive-value") == "[REDACTED]")
        #expect(SecretManager.redacted("").isEmpty)
        #expect(SecretManager.redactedMetadata(["apiKey": "secret", "provider": "finnhub"]) == ["apiKey": "[REDACTED]", "provider": "finnhub"])
    }

    @Test("Typed provider access is available")
    func typedProviderAccess() {
        let manager = SecretManager(environment: ["OLLAMA_ENDPOINT": "http://localhost:11434"], keychainLookup: { _ in nil }, localValues: [:], exampleValues: [:])
        #expect(manager.ollamaEndpoint == "http://localhost:11434")
        #expect(manager.value(for: .ollamaEndpoint) == "http://localhost:11434")
    }
}
