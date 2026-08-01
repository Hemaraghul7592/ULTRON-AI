import Foundation

// MARK: - Filing

public struct SEBIFiling: Sendable, Codable, Identifiable {
    public let id: String
    public let company: String; public let symbol: String; public let isin: String
    public let exchange: SEBIExchange; public let category: SEBICategory
    public let title: String; public let description: String
    public let date: Date; public let source: String; public let url: String
    public let documentType: String; public let documentID: String
    public let parsedContent: String; public let metadata: [String: String]

    public init(id: String = UUID().uuidString, company: String, symbol: String = "", isin: String = "", exchange: SEBIExchange = .nse, category: SEBICategory = .corporateAnnouncement, title: String, description: String = "", date: Date = Date(), source: String = "", url: String = "", documentType: String = "", documentID: String = "", parsedContent: String = "", metadata: [String: String] = [:]) {
        self.id = id; self.company = company; self.symbol = symbol; self.isin = isin; self.exchange = exchange
        self.category = category; self.title = title; self.description = description; self.date = date
        self.source = source; self.url = url; self.documentType = documentType; self.documentID = documentID
        self.parsedContent = parsedContent; self.metadata = metadata
    }
}

public enum SEBIExchange: String, Sendable, Codable, CaseIterable { case nse, bse, both }

public enum SEBICategory: String, Sendable, Codable, CaseIterable {
    case corporateAnnouncement, shareholdingPattern, insiderTrading, bulkDeal, blockDeal
    case boardMeeting, annualReport, quarterlyResult, dividend, bonus, rightsIssue, stockSplit
    case buyback, merger, acquisition, delisting, listing, preferentialAllotment, esop
    case votingResult, postalBallot, creditRatingUpdate, promoterActivity
}

// MARK: - Company Profile

public struct SEBICompanyProfile: Sendable, Codable, Identifiable {
    public let id = UUID(); public let symbol: String; public let isin: String
    public let companyName: String; public let exchange: SEBIExchange
    public let sector: String; public let listingDate: Date?
    public var latestFiling: Date?; public var filingCount: Int

    public init(symbol: String, isin: String = "", companyName: String, exchange: SEBIExchange = .nse, sector: String = "", listingDate: Date? = nil) {
        self.symbol = symbol; self.isin = isin; self.companyName = companyName; self.exchange = exchange
        self.sector = sector; self.listingDate = listingDate; filingCount = 0
    }
}

// MARK: - Analysis

public struct SEBIAnalysisResult: Sendable, Codable {
    public let filing: SEBIFiling
    public let summary: String; public let risks: [String]; public let opportunities: [String]
    public let marketImpact: String; public let longTermImplications: String; public let confidence: Double
    public init(filing: SEBIFiling, summary: String = "", risks: [String] = [], opportunities: [String] = [], marketImpact: String = "", longTermImplications: String = "", confidence: Double = 0) {
        self.filing = filing; self.summary = summary; self.risks = risks; self.opportunities = opportunities
        self.marketImpact = marketImpact; self.longTermImplications = longTermImplications; self.confidence = confidence
    }
}
