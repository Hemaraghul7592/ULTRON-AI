import Foundation

/// Assembles multiple charts into complete dashboards.
public enum DashboardEngine {

    public static func portfolioDashboard(
        snapshots: [PerformanceSnapshot], holdings: [(symbol: String, value: Double)], bars: [OHLCV]
    ) -> Dashboard {
        var charts: [ChartData] = []
        if !snapshots.isEmpty { charts.append(ChartDataBuilder.portfolioValueHistory(snapshots: snapshots)) }
        if !holdings.isEmpty { charts.append(ChartDataBuilder.assetAllocation(holdings: holdings)) }
        if !snapshots.isEmpty { charts.append(ChartDataBuilder.portfolioGrowth(history: snapshots)) }
        if !bars.isEmpty { charts.append(ChartDataBuilder.candlestickChart(bars: bars, title: "Portfolio Price")) }
        return Dashboard(title: "Portfolio Dashboard", charts: charts)
    }

    public static func marketDashboard(
        bars: [OHLCV], indices: [MarketIndex], title: String = "Market Dashboard"
    ) -> Dashboard {
        var charts: [ChartData] = []
        if !bars.isEmpty {
            charts.append(ChartDataBuilder.candlestickChart(bars: bars, title: "Price Action"))
            charts.append(ChartDataBuilder.volumeChart(bars: bars))
        }
        if !indices.isEmpty { charts.append(ChartDataBuilder.indicesPerformance(indices: indices)) }
        return Dashboard(title: title, charts: charts)
    }

    public static func technicalDashboard(
        bars: [OHLCV], rsi: RSIRresult?, macd: MACDResult?, bb: BollingerBands?, title: String = "Technical Dashboard"
    ) -> Dashboard {
        var charts: [ChartData] = []
        if !bars.isEmpty { charts.append(ChartDataBuilder.candlestickChart(bars: bars, title: "Candlestick")) }
        if let r = rsi { charts.append(ChartDataBuilder.rsiChart(rsi: r)) }
        if let m = macd { charts.append(ChartDataBuilder.macdChart(macd: m)) }
        if let b = bb { charts.append(ChartDataBuilder.bollingerChart(bb: b, title: "Bollinger Bands")) }
        return Dashboard(title: title, charts: charts)
    }

    public static func fundamentalDashboard(
        statements: [IncomeStatement], score: FundamentalScore?, title: String = "Fundamental Dashboard"
    ) -> Dashboard {
        var charts: [ChartData] = []
        if !statements.isEmpty {
            charts.append(ChartDataBuilder.revenueGrowth(statements: statements))
            charts.append(ChartDataBuilder.epsTrend(statements: statements))
        }
        if let s = score { charts.append(ChartDataBuilder.financialHealthScore(score: s)) }
        return Dashboard(title: title, charts: charts)
    }

    public static func fullDashboard(
        snapshots: [PerformanceSnapshot], holdings: [(symbol: String, value: Double)],
        bars: [OHLCV], indices: [MarketIndex], rsi: RSIRresult?, macd: MACDResult?,
        bb: BollingerBands?, statements: [IncomeStatement], score: FundamentalScore?,
        config: DashboardConfig = .all
    ) -> Dashboard {
        var charts: [ChartData] = []
        if config.includePortfolio { charts.append(contentsOf: portfolioDashboard(snapshots: snapshots, holdings: holdings, bars: bars).charts) }
        if config.includeMarket { charts.append(contentsOf: marketDashboard(bars: bars, indices: indices).charts) }
        if config.includeTechnical { charts.append(contentsOf: technicalDashboard(bars: bars, rsi: rsi, macd: macd, bb: bb).charts) }
        if config.includeFundamental { charts.append(contentsOf: fundamentalDashboard(statements: statements, score: score).charts) }
        return Dashboard(title: "ULTRON Dashboard", charts: charts)
    }
}
