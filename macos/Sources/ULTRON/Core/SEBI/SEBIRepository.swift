import Foundation

/// Repository for SEBI filings with caching, search, and filtering.
public actor SEBIRepository {
    private var filings: [SEBIFiling] = []
    private var profiles: [String: SEBICompanyProfile] = [:]
    private var keywordIndex: [String: Set<String>] = [:]
    private let maxFilings: Int

    public init(maxFilings: Int = 10000) { self.maxFilings = maxFilings }

    // MARK: - Store

    public func add(_ filing: SEBIFiling) -> Bool {
        guard !SEBIParser.isDuplicate(filing, existing: filings) else { return false }
        filings.append(filing)
        if filings.count > maxFilings { filings.removeFirst(filings.count - maxFilings) }

        var profile = profiles[filing.symbol] ?? SEBICompanyProfile(symbol: filing.symbol, isin: filing.isin, companyName: filing.company, exchange: filing.exchange)
        profile.latestFiling = filing.date; profile.filingCount += 1
        profiles[filing.symbol] = profile

        for keyword in SEBIParser.extractKeywords(filing.parsedContent) {
            keywordIndex[keyword, default: []].insert(filing.id)
        }
        return true
    }

    public func addBatch(_ batch: [SEBIFiling]) -> Int {
        batch.filter { add($0) }.count
    }

    // MARK: - Query

    public func get(id: String) -> SEBIFiling? { filings.first { $0.id == id } }
    public func recent(limit: Int = 50) -> [SEBIFiling] { Array(filings.suffix(limit)).reversed() }

    public func search(keyword: String) -> [SEBIFiling] {
        let ids = keywordIndex[keyword.lowercased()] ?? []
        return filings.filter { ids.contains($0.id) }
    }

    public func filter(symbol: String? = nil, category: SEBICategory? = nil, exchange: SEBIExchange? = nil, from: Date? = nil, to: Date? = nil) -> [SEBIFiling] {
        filings.filter { f in
            (symbol == nil || f.symbol == symbol!) &&
            (category == nil || f.category == category!) &&
            (exchange == nil || f.exchange == exchange!) &&
            (from == nil || f.date >= from!) &&
            (to == nil || f.date <= to!)
        }
    }

    public func bySymbol(_ symbol: String) -> [SEBIFiling] { filter(symbol: symbol) }
    public func byCategory(_ category: SEBICategory) -> [SEBIFiling] { filter(category: category) }
    public func profile(for symbol: String) -> SEBICompanyProfile? { profiles[symbol] }
    public var count: Int { filings.count }
    public var allSymbols: [String] { Array(profiles.keys).sorted() }
}
