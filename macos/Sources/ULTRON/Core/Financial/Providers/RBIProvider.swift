import Foundation

/// RBI (Reserve Bank of India) economic data provider.
///
/// Wraps the RBI CIMS Gateway for Indian financial and economic data.
/// An existing Python implementation lives at:
/// `/Users/raghul/Desktop/RBI PROVIDER/rbi_economic_provider/`
///
/// This Swift provider mirrors the Python API surface while conforming
/// to ULTRON's `FinancialProvider` protocol.
public actor RBIProvider: FinancialProvider {
    public let providerID = "rbi"
    public let providerName = "RBI"
    public let financialCapabilities: Set<FinancialCapability> = [.fundamentals, .news]
    public let category: ServiceCategory = .custom

    private let endpoint: String
    private let session: URLSession
    private var isAvailable = false

    public init(endpoint: String? = nil) {
        self.endpoint = endpoint ?? "http://localhost:8500"
        session = URLSession(configuration: .ephemeral)
    }

    public func initialize() async throws {
        isAvailable = await checkAvailability()
    }

    public func healthCheck() async -> HealthStatus { isAvailable ? .healthy : .unhealthy }
    public func shutdown() async { session.invalidateAndCancel() }

    public func fetchQuote(symbol: String) async throws -> Quote { throw FinancialError.unsupportedCapability("quotes") }
    public func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { throw FinancialError.unsupportedCapability("ohlcv") }

    public func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        guard isAvailable else { throw FinancialError.providerNotAvailable("rbi") }
        return CompanyProfile(symbol: "INDIA", name: "Republic of India", sector: "Sovereign", marketCap: 3_500_000_000_000_000, country: "IN", currency: "INR")
    }

    public func fetchIndices() async throws -> [MarketIndex] {
        guard isAvailable else { throw FinancialError.providerNotAvailable("rbi") }
        return [MarketIndex(symbol: "IND_GDP", name: "India GDP", value: 3_500_000_000_000, change: 0, changePercent: 0)]
    }

    public func fetchNews(symbols: [String]) async throws -> [NewsArticle] {
        guard isAvailable else { return [] }
        return [NewsArticle(title: "RBI Monetary Policy", summary: "Current policy data available via RBI provider.", source: "RBI", publishedAt: Date())]
    }

    // MARK: - RBI-Specific Methods

    public func fetchCPI(startDate: String? = nil, endDate: String? = nil) async throws -> [String: Any] {
        try await fetch(endpoint + "/cpi" + dateParams(start: startDate, end: endDate))
    }

    public func fetchWPI(startDate: String? = nil, endDate: String? = nil) async throws -> [String: Any] {
        try await fetch(endpoint + "/wpi" + dateParams(start: startDate, end: endDate))
    }

    public func fetchExchangeRate(currency: String = "USD", startDate: String? = nil, endDate: String? = nil) async throws -> [String: Any] {
        try await fetch(endpoint + "/exchange-rate/\(currency)" + dateParams(start: startDate, end: endDate))
    }

    public func fetchMonetaryPolicy(startDate: String? = nil, endDate: String? = nil) async throws -> [String: Any] {
        try await fetch(endpoint + "/monetary-policy" + dateParams(start: startDate, end: endDate))
    }

    public func fetchGDP(startDate: String? = nil, endDate: String? = nil) async throws -> [String: Any] {
        try await fetch(endpoint + "/gdp" + dateParams(start: startDate, end: endDate))
    }

    public func listSeries() async throws -> [String: Any] {
        try await fetch(endpoint + "/series")
    }

    // MARK: - Helpers

    private func fetch(_ urlString: String) async throws -> [String: Any] {
        guard let url = URL(string: urlString) else { throw FinancialError.invalidData("Invalid URL") }
        let (data, response) = try await session.data(from: url)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else {
            throw FinancialError.invalidData("RBI returned non-200")
        }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw FinancialError.invalidData("RBI response is not JSON")
        }
        return json
    }

    private func dateParams(start: String?, end: String?) -> String {
        var params: [String] = []
        if let s = start { params.append("start_date=\(s)") }
        if let e = end { params.append("end_date=\(e)") }
        return params.isEmpty ? "" : "?" + params.joined(separator: "&")
    }

    private func checkAvailability() async -> Bool {
        guard let url = URL(string: "\(endpoint)/health") else { return false }
        do {
            let (_, response) = try await session.data(from: url)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
}
