import Charts
import SwiftUI

public struct PerformanceChartCard: View {
    private let chart: ChartData?
    private let state: DashboardCardState

    public init(chart: ChartData?, state: DashboardCardState) {
        self.chart = chart
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "Portfolio Performance", subtitle: "Recent portfolio history", icon: "waveform.path.ecg", tint: .blue, state: state) {
            if let chart, !chart.points.isEmpty {
                Chart(chart.points) { point in
                    LineMark(
                        x: .value("Date", point.timestamp ?? Date()),
                        y: .value("Value", point.value)
                    )
                    .foregroundStyle(.blue.gradient)
                    AreaMark(
                        x: .value("Date", point.timestamp ?? Date()),
                        y: .value("Value", point.value)
                    )
                    .foregroundStyle(.blue.opacity(0.14).gradient)
                }
                .chartXAxis(.hidden)
                .chartYAxis {
                    AxisMarks(position: .leading) { value in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5)).foregroundStyle(.white.opacity(0.1))
                        AxisValueLabel().foregroundStyle(.secondary)
                    }
                }
                .frame(height: 150)
                .accessibilityLabel("Portfolio performance chart")
            } else {
                EmptyStateCard(title: "Performance history is not available.", icon: "chart.line.uptrend.xyaxis")
            }
        }
    }
}
