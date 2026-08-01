import Foundation

/// Configuration for the Financial module.
public struct FinancialConfig: Sendable {

    /// Default provider priority order for quotes.
    public let quoteProviderPriority: [String]

    /// Default provider priority order for OHLCV.
    public let ohlcvProviderPriority: [String]

    /// Default provider priority order for company data.
    public let companyProviderPriority: [String]

    /// Default cache TTL for real-time quotes (seconds).
    public let quoteCacheTTL: TimeInterval

    /// Default cache TTL for OHLCV data (seconds).
    public let ohlcvCacheTTL: TimeInterval

    /// Default cache TTL for company profiles (seconds).
    public let companyCacheTTL: TimeInterval

    /// Supported exchanges.
    public let supportedExchanges: Set<String>

    /// Default currency.
    public let defaultCurrency: String

    public init(
        quoteProviderPriority: [String] = [],
        ohlcvProviderPriority: [String] = [],
        companyProviderPriority: [String] = [],
        quoteCacheTTL: TimeInterval = 60,
        ohlcvCacheTTL: TimeInterval = 3600,
        companyCacheTTL: TimeInterval = 86400,
        supportedExchanges: Set<String> = ["NSE", "BSE", "NYSE", "NASDAQ"],
        defaultCurrency: String = "USD"
    ) {
        self.quoteProviderPriority = quoteProviderPriority
        self.ohlcvProviderPriority = ohlcvProviderPriority
        self.companyProviderPriority = companyProviderPriority
        self.quoteCacheTTL = quoteCacheTTL
        self.ohlcvCacheTTL = ohlcvCacheTTL
        self.companyCacheTTL = companyCacheTTL
        self.supportedExchanges = supportedExchanges
        self.defaultCurrency = defaultCurrency
    }
}
