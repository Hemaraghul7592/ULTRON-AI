import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite struct VisualizationTests {

    // MARK: - Chart Data Builder

    @Test("Portfolio value history produces chart") func testPortfolioValue() {
        let snapshots = [PerformanceSnapshot(date: Date(), totalValue: 10000, dailyReturn: 0.02, cumulativeReturn: 0.05, holdingsCount: 5)]
        let chart = ChartDataBuilder.portfolioValueHistory(snapshots: snapshots)
        #expect(chart.type == .line)
        #expect(chart.points.count == 1)
        #expect(chart.title == "Portfolio Value")
    }

    @Test("Asset allocation produces pie segments") func testAssetAllocation() {
        let holdings: [(String, Double)] = [("AAPL", 5000), ("GOOGL", 3000), ("TSLA", 2000)]
        let chart = ChartDataBuilder.assetAllocation(holdings: holdings)
        #expect(chart.type == .pie)
        #expect(chart.segments.count == 3)
    }

    @Test("Asset allocation with zeros returns empty") func testAssetAllocationEmpty() {
        let chart = ChartDataBuilder.assetAllocation(holdings: [])
        #expect(chart.type == .pie)
        #expect(chart.segments.isEmpty)
    }

    @Test("Candlestick chart from OHLCV") func testCandlestick() {
        let bars = [OHLCV(symbol: "AAPL", open: 150, high: 155, low: 149, close: 153, volume: 1_000_000, timestamp: Date())]
        let chart = ChartDataBuilder.candlestickChart(bars: bars, title: "AAPL")
        #expect(chart.type == .candlestick)
        #expect(chart.candlesticks.count == 1)
        #expect(chart.candlesticks[0].open == 150)
    }

    @Test("Volume chart from OHLCV") func testVolume() {
        let bars = [OHLCV(symbol: "AAPL", open: 150, high: 155, low: 149, close: 153, volume: 1_000_000, timestamp: Date())]
        let chart = ChartDataBuilder.volumeChart(bars: bars)
        #expect(chart.type == .volume)
        #expect(chart.points[0].value == 1_000_000)
    }

    @Test("Revenue growth chart") func testRevenue() {
        let statements = [
            IncomeStatement(symbol: "AAPL", fiscalYear: 2023, period: .annual, revenue: 383_000_000_000, costOfRevenue: 220_000_000_000, operatingExpenses: 55_000_000_000, operatingIncome: 108_000_000_000, netIncome: 97_000_000_000),
            IncomeStatement(symbol: "AAPL", fiscalYear: 2024, period: .annual, revenue: 400_000_000_000, costOfRevenue: 230_000_000_000, operatingExpenses: 58_000_000_000, operatingIncome: 112_000_000_000, netIncome: 100_000_000_000),
        ]
        let chart = ChartDataBuilder.revenueGrowth(statements: statements)
        #expect(chart.type == .bar)
        #expect(chart.points.count == 2)
    }

    @Test("EPS trend chart") func testEPSTrend() {
        let statements = [
            IncomeStatement(symbol: "AAPL", fiscalYear: 2024, period: .annual, revenue: 100, costOfRevenue: 60, operatingExpenses: 20, operatingIncome: 20, netIncome: 15, eps: 6.5),
        ]
        let chart = ChartDataBuilder.epsTrend(statements: statements)
        #expect(chart.points[0].value == 6.5)
    }

    @Test("Profit margins chart") func testProfitMargins() {
        let stmt = IncomeStatement(symbol: "AAPL", fiscalYear: 2024, period: .annual, revenue: 100, costOfRevenue: 60, operatingExpenses: 20, operatingIncome: 20, netIncome: 15)
        let chart = ChartDataBuilder.profitMargins(statement: stmt)
        #expect(chart.segments.count == 3)
    }

    // MARK: - Dashboard Engine

    @Test("Portfolio dashboard assembles charts") func testDashboard() {
        let snapshots = [PerformanceSnapshot(date: Date(), totalValue: 10000)]
        let bars = [OHLCV(symbol: "AAPL", open: 150, high: 155, low: 149, close: 153, volume: 1_000_000, timestamp: Date())]
        let dashboard = DashboardEngine.portfolioDashboard(snapshots: snapshots, holdings: [("AAPL", 5000)], bars: bars)
        #expect(dashboard.title == "Portfolio Dashboard")
        #expect(!dashboard.charts.isEmpty)
    }

    @Test("Market dashboard assembles charts") func testMarketDashboard() {
        let bars = [OHLCV(symbol: "AAPL", open: 150, high: 155, low: 149, close: 153, volume: 1_000_000, timestamp: Date())]
        let dashboard = DashboardEngine.marketDashboard(bars: bars, indices: [])
        #expect(dashboard.title == "Market Dashboard")
        #expect(dashboard.charts.count >= 2)
    }

    @Test("Full dashboard with all config") func testFullDashboard() {
        let snapshots = [PerformanceSnapshot(date: Date(), totalValue: 10000)]
        let bars = [OHLCV(symbol: "AAPL", open: 150, high: 155, low: 149, close: 153, volume: 1_000_000, timestamp: Date())]
        let dashboard = DashboardEngine.fullDashboard(snapshots: snapshots, holdings: [("AAPL", 5000)], bars: bars, indices: [], rsi: nil, macd: nil, bb: nil, statements: [], score: nil)
        #expect(!dashboard.charts.isEmpty)
    }

    // MARK: - Export

    @Test("CSV export produces data") func testCSVExport() {
        let engine = VisualizationEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let chart = ChartData(title: "Test", type: .line, points: [ChartPoint(label: "A", value: 100)])
        let exported = engine.exportCSV(chart)
        #expect(exported != nil)
        #expect(exported!.format == .csv)
        #expect(exported!.data.count > 0)
    }

    @Test("JSON export produces data") func testJSONExport() {
        let engine = VisualizationEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let chart = ChartData(title: "Test", type: .line, points: [ChartPoint(label: "A", value: 100)])
        let exported = engine.exportJSON(chart)
        #expect(exported != nil)
        #expect(exported!.format == .json)
    }

    @Test("CSV export empty chart") func testCSVEmpty() {
        let engine = VisualizationEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
        let chart = ChartData(title: "Empty", type: .line)
        let exported = engine.exportCSV(chart)
        #expect(exported != nil)
    }
}
