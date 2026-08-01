import Foundation

/// Central entry point for all visualization operations.
///
/// Consumes outputs from FinancialEngine, PortfolioEngine,
/// TechnicalAnalysisEngine, and FundamentalAnalysisEngine.
/// Produces ChartData and Dashboard structs for SwiftUI rendering.
@MainActor
public final class VisualizationEngine {

    private let logger: Logger

    public init(logger: Logger) { self.logger = logger }

    // MARK: - Charts

    public func portfolioValueChart(_ snapshots: [PerformanceSnapshot]) -> ChartData {
        ChartDataBuilder.portfolioValueHistory(snapshots: snapshots)
    }

    public func assetAllocationChart(_ holdings: [(symbol: String, value: Double)]) -> ChartData {
        ChartDataBuilder.assetAllocation(holdings: holdings)
    }

    public func candlestickChart(_ bars: [OHLCV], title: String = "Candlestick") -> ChartData {
        ChartDataBuilder.candlestickChart(bars: bars, title: title)
    }

    public func rsiChart(_ rsi: RSIRresult) -> ChartData {
        ChartDataBuilder.rsiChart(rsi: rsi)
    }

    public func macdChart(_ macd: MACDResult) -> ChartData {
        ChartDataBuilder.macdChart(macd: macd)
    }

    public func revenueChart(_ statements: [IncomeStatement]) -> ChartData {
        ChartDataBuilder.revenueGrowth(statements: statements)
    }

    public func healthScoreChart(_ score: FundamentalScore) -> ChartData {
        ChartDataBuilder.financialHealthScore(score: score)
    }

    // MARK: - Dashboards

    public func portfolioDashboard(snapshots: [PerformanceSnapshot], holdings: [(symbol: String, value: Double)], bars: [OHLCV]) -> Dashboard {
        DashboardEngine.portfolioDashboard(snapshots: snapshots, holdings: holdings, bars: bars)
    }

    public func marketDashboard(bars: [OHLCV], indices: [MarketIndex]) -> Dashboard {
        DashboardEngine.marketDashboard(bars: bars, indices: indices)
    }

    public func technicalDashboard(bars: [OHLCV], rsi: RSIRresult?, macd: MACDResult?, bb: BollingerBands?) -> Dashboard {
        DashboardEngine.technicalDashboard(bars: bars, rsi: rsi, macd: macd, bb: bb)
    }

    public func fullDashboard(
        snapshots: [PerformanceSnapshot], holdings: [(symbol: String, value: Double)],
        bars: [OHLCV], indices: [MarketIndex], rsi: RSIRresult?, macd: MACDResult?,
        bb: BollingerBands?, statements: [IncomeStatement], score: FundamentalScore?
    ) -> Dashboard {
        DashboardEngine.fullDashboard(snapshots: snapshots, holdings: holdings, bars: bars, indices: indices, rsi: rsi, macd: macd, bb: bb, statements: statements, score: score)
    }

    // MARK: - Export

    public func exportCSV(_ chart: ChartData) -> ExportedChart? {
        var lines = ["label,value"]
        for pt in chart.points { lines.append("\(pt.label),\(pt.value)") }
        guard let data = lines.joined(separator: "\n").data(using: .utf8) else { return nil }
        return ExportedChart(format: .csv, data: data, chartTitle: chart.title)
    }

    public func exportJSON(_ chart: ChartData) -> ExportedChart? {
        guard let data = try? JSONEncoder().encode(chart) else { return nil }
        return ExportedChart(format: .json, data: data, chartTitle: chart.title)
    }
}
