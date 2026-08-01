import Foundation

/// Loads API credentials from the bundled APIKeys.plist.
///
/// Credentials are loaded once at startup and accessed via `shared`.
/// Never access the plist directly from provider code — always go
/// through this configuration.
public final class APIConfiguration: Sendable {

    public static let shared = APIConfiguration()

    private let dict: [String: String]

    private init() {
        guard let url = Bundle.module.url(forResource: "APIKeys", withExtension: "plist"),
              let data = try? Data(contentsOf: url),
              let plist = try? PropertyListSerialization.propertyList(from: data, format: nil) as? [String: String]
        else {
            dict = [:]
            return
        }
        dict = plist
    }

    private func value(_ key: String) -> String { dict[key] ?? "" }

    public var finnhubKey: String { value("FINNHUB_API_KEY") }
    public var newsAPIKey: String { value("NEWS_API_KEY") }
    public var marketauxToken: String { value("MARKETAUX_API_TOKEN") }
    public var binanceApiKey: String { value("BINANCE_API_KEY") }
    public var binanceSecret: String { value("BINANCE_SECRET_KEY") }
    public var openRouterKey: String { value("OPENROUTER_API_KEY") }
    public var ollamaEndpoint: String { value("OLLAMA_ENDPOINT") }
    public var hackerEarthKey: String { value("HACKEREARTH_API_KEY") }
    public var hackerEarthSecret: String { value("HACKEREARTH_SECRET_KEY") }
}
