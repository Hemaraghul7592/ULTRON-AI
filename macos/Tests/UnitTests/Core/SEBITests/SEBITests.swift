import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite struct SEBITests {

    // MARK: - Parser

    @Test("HTML parsing removes tags") func testHTMLParse() {
        let html = "<p>Hello <b>World</b></p>"
        let result = SEBIParser.parseHTML(html)
        #expect(result == "Hello World")
    }

    @Test("HTML entities decoded") func testHTMLEntities() {
        let html = "Price &amp; Value &lt; 100"
        #expect(SEBIParser.parseHTML(html) == "Price & Value < 100")
    }

    @Test("Normalize collapses whitespace") func testNormalize() {
        #expect(SEBIParser.normalize("  Hello   World  ") == "hello world")
    }

    @Test("Duplicate detection works") func testDuplicate() {
        let a = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4 Results", date: Date())
        let b = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4 results", date: Date())
        #expect(SEBIParser.isDuplicate(b, existing: [a]))
    }

    @Test("Duplicate detection with different title") func testNotDuplicate() {
        let a = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q3 Results", date: Date())
        let b = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4 Results", date: Date())
        #expect(!SEBIParser.isDuplicate(b, existing: [a]))
    }

    @Test("Keyword extraction") func testKeywords() {
        let keywords = SEBIParser.extractKeywords("Reliance Industries Ltd Q4 FY2024 Results")
        #expect(keywords.contains("reliance"))
        #expect(keywords.contains("results"))
    }

    // MARK: - Repository

    @Test("Repository add and retrieve") func testRepoAdd() async {
        let repo = SEBIRepository(maxFilings: 100)
        let filing = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4 Results", parsedContent: "quarterly results fy2024")
        #expect(await repo.add(filing))
        #expect(await repo.count == 1)
    }

    @Test("Repository prevents duplicates") func testRepoDuplicate() async {
        let repo = SEBIRepository(maxFilings: 100)
        let a = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4 Results", date: Date())
        _ = await repo.add(a)
        #expect(!(await repo.add(a)))
    }

    @Test("Repository search by keyword") func testRepoSearch() async {
        let repo = SEBIRepository(maxFilings: 100)
        let filing = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4 Results", parsedContent: "revenue growth profit")
        _ = await repo.add(filing)
        #expect(await repo.search(keyword: "revenue").count == 1)
    }

    @Test("Repository filter by symbol") func testRepoFilterSymbol() async {
        let repo = SEBIRepository(maxFilings: 100)
        _ = await repo.add(SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "T1"))
        _ = await repo.add(SEBIFiling(company: "INFY", symbol: "INFY", category: .annualReport, title: "A1"))
        #expect(await repo.bySymbol("TCS").count == 1)
    }

    @Test("Repository filter by category") func testRepoFilterCategory() async {
        let repo = SEBIRepository(maxFilings: 100)
        _ = await repo.add(SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "T1"))
        _ = await repo.add(SEBIFiling(company: "TCS", symbol: "TCS", category: .dividend, title: "D1"))
        #expect(await repo.byCategory(.dividend).count == 1)
    }

    @Test("Repository batch add") func testRepoBatch() async {
        let repo = SEBIRepository(maxFilings: 100)
        let batch = [
            SEBIFiling(company: "A", symbol: "A", category: .quarterlyResult, title: "Q1"),
            SEBIFiling(company: "B", symbol: "B", category: .annualReport, title: "AR"),
        ]
        #expect(await repo.addBatch(batch) == 2)
    }

    @Test("Repository profile tracking") func testRepoProfile() async {
        let repo = SEBIRepository(maxFilings: 100)
        _ = await repo.add(SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q1"))
        _ = await repo.add(SEBIFiling(company: "TCS", symbol: "TCS", category: .annualReport, title: "AR"))
        let profile = await repo.profile(for: "TCS")
        #expect(profile != nil)
        #expect(profile?.filingCount == 2)
    }

    // MARK: - SEBI Engine

    @Test("Engine ingest and query") func testEngineIngest() async {
        let engine = SEBIEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let filing = SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4 Results", parsedContent: "results")
        #expect(await engine.ingest(filing))
        #expect(await engine.filingCount() == 1)
        #expect(await engine.bySymbol("TCS").count == 1)
    }

    @Test("Engine search") func testEngineSearch() async {
        let engine = SEBIEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        await engine.ingest(SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Results", parsedContent: "revenue growth"))
        #expect(await engine.search(keyword: "revenue").count == 1)
    }

    @Test("Engine filing stats") func testEngineStats() async {
        let engine = SEBIEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        await engine.ingest(SEBIFiling(company: "A", symbol: "A", category: .quarterlyResult, title: "Q1"))
        await engine.ingest(SEBIFiling(company: "B", symbol: "B", category: .dividend, title: "Div"))
        let stats = await engine.filingStats()
        #expect(!stats.isEmpty)
    }

    @Test("Engine timeline data") func testEngineTimeline() async {
        let engine = SEBIEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let now = Date()
        await engine.ingest(SEBIFiling(company: "TCS", symbol: "TCS", category: .quarterlyResult, title: "Q4", date: now))
        await engine.ingest(SEBIFiling(company: "INFY", symbol: "INFY", category: .annualReport, title: "AR", date: now.addingTimeInterval(-86400)))
        let timeline = await engine.timelineData(from: now.addingTimeInterval(-100000), to: now.addingTimeInterval(1))
        #expect(timeline.count == 2)
    }

    @Test("Engine relevant to portfolio") func testEnginePortfolio() async {
        let engine = SEBIEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        await engine.ingest(SEBIFiling(company: "TCS", symbol: "TCS", category: .dividend, title: "Dividend"))
        await engine.ingest(SEBIFiling(company: "INFY", symbol: "INFY", category: .quarterlyResult, title: "Q3"))
        let relevant = await engine.relevantToPortfolio(symbols: ["TCS"])
        #expect(relevant.count == 1)
    }
}
