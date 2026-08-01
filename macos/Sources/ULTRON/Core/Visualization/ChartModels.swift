import Foundation

// MARK: - Chart Data Points

public struct ChartPoint: Sendable, Codable, Identifiable {
    public let id = UUID()
    public let label: String
    public let value: Double
    public let secondary: Double?
    public let timestamp: Date?

    public init(label: String, value: Double, secondary: Double? = nil, timestamp: Date? = nil) {
        self.label = label; self.value = value; self.secondary = secondary; self.timestamp = timestamp
    }
}

public struct CandlestickPoint: Sendable, Codable, Identifiable {
    public let id = UUID()
    public let label: String; public let timestamp: Date
    public let open: Double; public let high: Double; public let low: Double; public let close: Double; public let volume: Int64
    public init(label: String = "", timestamp: Date, open: Double, high: Double, low: Double, close: Double, volume: Int64 = 0) {
        self.label = label; self.timestamp = timestamp; self.open = open; self.high = high; self.low = low; self.close = close; self.volume = volume
    }
}

// MARK: - Chart Types

public enum ChartType: String, Sendable, Codable, CaseIterable {
    case line, area, candlestick, ohlc, bar, volume, pie, donut, scatter, heatmap, treemap, timeline, allocation, risk, correlation
}

public struct ChartData: Sendable, Codable, Identifiable {
    public let id = UUID()
    public let title: String; public let type: ChartType
    public let points: [ChartPoint]; public let candlesticks: [CandlestickPoint]
    public let segments: [SegmentData]; public let xLabel: String; public let yLabel: String

    public init(title: String, type: ChartType = .line, points: [ChartPoint] = [], candlesticks: [CandlestickPoint] = [], segments: [SegmentData] = [], xLabel: String = "", yLabel: String = "") {
        self.title = title; self.type = type; self.points = points; self.candlesticks = candlesticks
        self.segments = segments; self.xLabel = xLabel; self.yLabel = yLabel
    }
}

public struct SegmentData: Sendable, Codable {
    public let label: String; public let value: Double; public let color: String
    public init(label: String, value: Double, color: String = "") { self.label = label; self.value = value; self.color = color }
}

// MARK: - Dashboard

public struct Dashboard: Sendable, Codable, Identifiable {
    public let id = UUID(); public let title: String; public let charts: [ChartData]; public let timestamp: Date
    public init(title: String, charts: [ChartData] = [], timestamp: Date = Date()) { self.title = title; self.charts = charts; self.timestamp = timestamp }
}

public struct DashboardConfig: Sendable {
    public let includePortfolio: Bool; public let includeMarket: Bool; public let includeTechnical: Bool; public let includeFundamental: Bool
    public init(includePortfolio: Bool = true, includeMarket: Bool = true, includeTechnical: Bool = true, includeFundamental: Bool = true) {
        self.includePortfolio = includePortfolio; self.includeMarket = includeMarket; self.includeTechnical = includeTechnical; self.includeFundamental = includeFundamental
    }
    public static let all = DashboardConfig()
}

// MARK: - Export

public enum ExportFormat: String, Sendable, CaseIterable { case png, pdf, csv, json }

public struct ExportedChart: Sendable {
    public let format: ExportFormat; public let data: Data; public let chartTitle: String
    public init(format: ExportFormat, data: Data, chartTitle: String) { self.format = format; self.data = data; self.chartTitle = chartTitle }
}
