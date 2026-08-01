import Foundation

/// Builds chart-ready data from engine outputs. Pure transformations — no calculations.
public enum ChartDataBuilder {

    // MARK: - Portfolio Charts

    public static func portfolioValueHistory(snapshots: [PerformanceSnapshot]) -> ChartData {
        let pts = snapshots.map { ChartPoint(label: ISO8601DateFormatter().string(from: $0.date), value: $0.totalValue, timestamp: $0.date) }
        return ChartData(title: "Portfolio Value", type: .line, points: pts, xLabel: "Date", yLabel: "Value ($)")
    }

    public static func assetAllocation(holdings: [(symbol: String, value: Double)]) -> ChartData {
        let total = holdings.reduce(0) { $0 + $1.value }
        guard total > 0 else { return ChartData(title: "Asset Allocation", type: .pie) }
        let colors = ["#4ECDC4", "#FF6B6B", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"]
        let segments = holdings.enumerated().map { i, h in SegmentData(label: h.symbol, value: h.value / total * 100, color: colors[i % colors.count]) }
        return ChartData(title: "Asset Allocation", type: .pie, segments: segments)
    }

    public static func portfolioGrowth(history: [PerformanceSnapshot]) -> ChartData {
        guard let first = history.first?.totalValue, first > 0 else { return ChartData(title: "Portfolio Growth", type: .line) }
        let pts = history.map { ChartPoint(label: ISO8601DateFormatter().string(from: $0.date), value: ($0.totalValue - first) / first * 100, timestamp: $0.date) }
        return ChartData(title: "Portfolio Growth %", type: .line, points: pts, xLabel: "Date", yLabel: "Growth (%)")
    }

    // MARK: - Market Charts

    public static func candlestickChart(bars: [OHLCV], title: String) -> ChartData {
        let candles = bars.map { CandlestickPoint(label: ISO8601DateFormatter().string(from: $0.timestamp), timestamp: $0.timestamp, open: $0.open, high: $0.high, low: $0.low, close: $0.close, volume: $0.volume) }
        return ChartData(title: title, type: .candlestick, candlesticks: candles)
    }

    public static func volumeChart(bars: [OHLCV]) -> ChartData {
        let pts = bars.map { ChartPoint(label: ISO8601DateFormatter().string(from: $0.timestamp), value: Double($0.volume), timestamp: $0.timestamp) }
        return ChartData(title: "Volume", type: .volume, points: pts, xLabel: "Date", yLabel: "Volume")
    }

    // MARK: - Technical Charts

    public static func rsiChart(rsi: RSIRresult) -> ChartData {
        let pts = rsi.values.map { ChartPoint(label: ISO8601DateFormatter().string(from: $0.timestamp), value: $0.value, timestamp: $0.timestamp) }
        return ChartData(title: "RSI (\(rsi.period))", type: .line, points: pts, xLabel: "Date", yLabel: "RSI")
    }

    public static func macdChart(macd: MACDResult) -> ChartData {
        var pts: [ChartPoint] = []
        for i in 0..<macd.macdLine.count {
            let sig = i < macd.signalLine.count ? macd.signalLine[i].value : nil
            pts.append(ChartPoint(label: ISO8601DateFormatter().string(from: macd.macdLine[i].timestamp), value: macd.macdLine[i].value, secondary: sig, timestamp: macd.macdLine[i].timestamp))
        }
        return ChartData(title: "MACD", type: .line, points: pts, xLabel: "Date", yLabel: "MACD")
    }

    public static func bollingerChart(bb: BollingerBands, title: String) -> ChartData {
        var pts: [ChartPoint] = []
        for i in 0..<bb.middle.count {
            let u = i < bb.upper.count ? bb.upper[i].value : nil
            pts.append(ChartPoint(label: ISO8601DateFormatter().string(from: bb.middle[i].timestamp), value: bb.middle[i].value, secondary: u, timestamp: bb.middle[i].timestamp))
        }
        return ChartData(title: title, type: .line, points: pts, xLabel: "Date", yLabel: "Price")
    }

    // MARK: - Fundamental Charts

    public static func revenueGrowth(statements: [IncomeStatement]) -> ChartData {
        let pts = statements.sorted { $0.fiscalYear < $1.fiscalYear }
            .map { ChartPoint(label: "\($0.fiscalYear)", value: $0.revenue) }
        return ChartData(title: "Revenue Growth", type: .bar, points: pts, xLabel: "Year", yLabel: "Revenue")
    }

    public static func epsTrend(statements: [IncomeStatement]) -> ChartData {
        let pts = statements.sorted { $0.fiscalYear < $1.fiscalYear }
            .map { ChartPoint(label: "\($0.fiscalYear)", value: $0.eps) }
        return ChartData(title: "EPS Trend", type: .bar, points: pts, xLabel: "Year", yLabel: "EPS")
    }

    public static func profitMargins(statement: IncomeStatement) -> ChartData {
        let gross = PortfolioCalculator.allocationPercent(holdingValue: statement.grossProfit, totalValue: statement.revenue)
        let operating = PortfolioCalculator.allocationPercent(holdingValue: statement.operatingIncome, totalValue: statement.revenue)
        let net = PortfolioCalculator.allocationPercent(holdingValue: statement.netIncome, totalValue: statement.revenue)
        let segments = [SegmentData(label: "Gross", value: gross, color: "#4ECDC4"), SegmentData(label: "Operating", value: operating, color: "#45B7D1"), SegmentData(label: "Net", value: net, color: "#96CEB4")]
        return ChartData(title: "Profit Margins", type: .bar, segments: segments, xLabel: "Margin Type", yLabel: "%")
    }

    public static func financialHealthScore(score: FundamentalScore) -> ChartData {
        let segments = score.components.map { SegmentData(label: $0.key, value: $0.value, color: "#4ECDC4") }
        return ChartData(title: "Financial Health", type: .bar, segments: segments, xLabel: "Category", yLabel: "Score")
    }

    // MARK: - Market Indices

    public static func indicesPerformance(indices: [MarketIndex]) -> ChartData {
        let pts = indices.map { ChartPoint(label: $0.name, value: $0.changePercent, timestamp: $0.timestamp) }
        return ChartData(title: "Indices Performance", type: .bar, points: pts, xLabel: "Index", yLabel: "Change (%)")
    }
}
