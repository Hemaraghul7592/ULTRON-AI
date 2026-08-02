import Foundation

/// Compatibility façade over `SecretManager`.
///
/// New code should use `SecretManager` directly.
public final class APIConfiguration: Sendable {

    public static let shared = APIConfiguration()
    private let secrets = SecretManager.shared
    private init() {}
    public var finnhubKey: String { secrets.finnhubKey }
    public var newsAPIKey: String { secrets.newsAPIKey }
    public var marketauxToken: String { secrets.marketauxToken }
    public var binanceApiKey: String { secrets.binanceAPIKey }
    public var binanceSecret: String { secrets.binanceSecret }
    public var openRouterKey: String { secrets.openRouterKey }
    public var ollamaEndpoint: String { secrets.ollamaEndpoint }
    public var hackerEarthKey: String { secrets.hackerEarthKey }
    public var hackerEarthSecret: String { secrets.hackerEarthSecret }
}
