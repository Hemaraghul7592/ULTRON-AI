import Foundation
import Security

public enum SecretKey: String, CaseIterable, Sendable {
    case finnhubAPIKey = "FINNHUB_API_KEY"
    case newsAPIKey = "NEWS_API_KEY"
    case marketauxToken = "MARKETAUX_API_TOKEN"
    case binanceAPIKey = "BINANCE_API_KEY"
    case binanceSecretKey = "BINANCE_SECRET_KEY"
    case openRouterAPIKey = "OPENROUTER_API_KEY"
    case ollamaEndpoint = "OLLAMA_ENDPOINT"
    case hackerEarthAPIKey = "HACKEREARTH_API_KEY"
    case hackerEarthSecretKey = "HACKEREARTH_SECRET_KEY"
}

public enum SecretManagerError: Error, CustomStringConvertible, Equatable {
    case missingRequiredSecret(SecretKey)
    case invalidLocalConfiguration

    public var description: String {
        switch self {
        case .missingRequiredSecret(let key): "Missing required secret: \(key.rawValue)"
        case .invalidLocalConfiguration: "Local secret configuration is invalid."
        }
    }
}

/// Resolves secrets without exposing a raw configuration dictionary.
///
/// Resolution order is environment, Keychain, local developer plist, then
/// placeholder example values. Example values are never considered secrets.
public final class SecretManager: @unchecked Sendable {
    public static let shared = SecretManager()

    private let values: [SecretKey: String]
    private let configurationError: SecretManagerError?

    public convenience init() {
        let environment = ProcessInfo.processInfo.environment
        let localURL = Self.localURL()
        let exampleURL = Self.exampleURL()
        let localResult = Self.readPlist(localURL)
        let exampleResult = Self.readPlist(exampleURL)
        let exampleValues = Self.defaultExampleValues().merging(exampleResult.values) { _, fileValue in fileValue }
        self.init(
            environment: environment,
            keychainLookup: { key in Self.keychainValue(key) },
            localValues: localResult.values,
            exampleValues: exampleValues,
            configurationError: localResult.error
        )
    }

    internal init(
        environment: [String: String],
        keychainLookup: @escaping @Sendable (SecretKey) -> String?,
        localValues: [String: String],
        exampleValues: [String: String],
        configurationError: SecretManagerError? = nil
    ) {
        var resolved: [SecretKey: String] = [:]
        for key in SecretKey.allCases {
            let candidates = [
                environment[key.rawValue],
                keychainLookup(key),
                localValues[key.rawValue],
                exampleValues[key.rawValue]
            ]
            resolved[key] = candidates.compactMap { value in
                guard let value, !Self.isPlaceholder(value) else { return nil }
                return value
            }.first ?? ""
        }
        values = resolved
        self.configurationError = configurationError
    }

    public var finnhubKey: String { value(.finnhubAPIKey) }
    public var newsAPIKey: String { value(.newsAPIKey) }
    public var marketauxToken: String { value(.marketauxToken) }
    public var binanceAPIKey: String { value(.binanceAPIKey) }
    public var binanceSecret: String { value(.binanceSecretKey) }
    public var openRouterKey: String { value(.openRouterAPIKey) }
    public var ollamaEndpoint: String { value(.ollamaEndpoint) }
    public var hackerEarthKey: String { value(.hackerEarthAPIKey) }
    public var hackerEarthSecret: String { value(.hackerEarthSecretKey) }

    public func value(for key: SecretKey) -> String { value(key) }

    public func validate(required keys: [SecretKey]) throws {
        if let configurationError { throw configurationError }
        for key in keys where value(key).isEmpty || Self.isPlaceholder(value(key)) {
            throw SecretManagerError.missingRequiredSecret(key)
        }
    }

    public static func isPlaceholder(_ value: String) -> Bool {
        let normalized = value.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        return normalized.isEmpty || normalized.hasPrefix("YOUR_") || normalized.hasPrefix("PLACEHOLDER") || normalized.hasPrefix("CHANGEME") || normalized.contains("<YOUR_")
    }

    public static func redacted(_ value: String) -> String {
        value.isEmpty ? "" : "[REDACTED]"
    }

    public static func redactedMetadata(_ metadata: [String: String]) -> [String: String] {
        metadata.reduce(into: [String: String]()) { result, item in
            let key = item.key.lowercased()
            result[item.key] = key.contains("api_key") || key.contains("apikey") || key.contains("token") || key.contains("secret") || key.contains("authorization") || key.contains("password") || key.contains("bearer") ? redacted(item.value) : item.value
        }
    }

    private func value(_ key: SecretKey) -> String { values[key] ?? "" }

    private static func localURL() -> URL? {
        if let configured = ProcessInfo.processInfo.environment["ULTRON_LOCAL_SECRETS_PATH"] {
            return URL(fileURLWithPath: configured)
        }
        let current = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent("APIKeys.local.plist")
        if FileManager.default.fileExists(atPath: current.path) { return current }
        guard let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first?.appendingPathComponent("ULTRON/APIKeys.local.plist"),
              FileManager.default.fileExists(atPath: appSupport.path) else { return nil }
        return appSupport
    }

    private static func exampleURL() -> URL? {
        if let configured = ProcessInfo.processInfo.environment["ULTRON_EXAMPLE_SECRETS_PATH"] {
            return URL(fileURLWithPath: configured)
        }
        let current = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent("APIKeys.example.plist")
        if FileManager.default.fileExists(atPath: current.path) { return current }
        return Bundle.main.url(forResource: "APIKeys.example", withExtension: "plist")
    }

    private static func readPlist(_ url: URL?) -> (values: [String: String], error: SecretManagerError?) {
        guard let url else { return ([:], nil) }
        do {
            let data = try Data(contentsOf: url)
            guard let values = try PropertyListSerialization.propertyList(from: data, format: nil) as? [String: String] else {
                return ([:], .invalidLocalConfiguration)
            }
            return (values, nil)
        } catch {
            return ([:], .invalidLocalConfiguration)
        }
    }

    private static func keychainValue(_ key: SecretKey) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "ai.ultron.secrets",
            kSecAttrAccount as String: key.rawValue,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private static func defaultExampleValues() -> [String: String] {
        [SecretKey.ollamaEndpoint.rawValue: "http://localhost:11434"]
    }
}
