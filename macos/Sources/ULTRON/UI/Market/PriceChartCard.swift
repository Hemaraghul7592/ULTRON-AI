import Charts
import SwiftUI

@MainActor
public struct PriceChartCard: View {
    let chart: ChartData?
    let range: MarketChartRange
    let state: DashboardCardState
    let onSelectRange: @MainActor @Sendable (MarketChartRange) -> Void

    public var body: some View {
        DashboardCard(title: "Price Chart", subtitle: "Native VisualizationEngine chart data", icon: "chart.xyaxis.line", tint: .cyan, state: state) {
            VStack(alignment: .leading, spacing: 12) {
                Picker("Range", selection: Binding(get: { range }, set: { onSelectRange($0) })) {
                    ForEach(MarketChartRange.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
                .controlSize(.small)
                .accessibilityLabel("Price chart range")

                if let chart, !chart.candlesticks.isEmpty {
                    Chart(chart.candlesticks) { candle in
                        RectangleMark(
                            x: .value("Date", candle.timestamp),
                            yStart: .value("Low", candle.low),
                            yEnd: .value("High", candle.high),
                            width: 2
                        )
                        .foregroundStyle(candle.close >= candle.open ? .green : .red)
                        BarMark(
                            x: .value("Date", candle.timestamp),
                            yStart: .value("Open", candle.open),
                            yEnd: .value("Close", candle.close),
                            width: 7
                        )
                        .foregroundStyle(candle.close >= candle.open ? .green : .red)
                    }
                    .chartXAxis(.hidden)
                    .chartYAxis(.hidden)
                    .frame(height: 190)
                    .accessibilityLabel("Price history chart for \(range.rawValue)")
                } else {
                    EmptyStateCard(title: "Price history is unavailable for this range.", icon: "chart.line.uptrend.xyaxis")
                }
            }
        }
    }
}
