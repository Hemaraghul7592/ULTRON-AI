import Charts
import SwiftUI

public struct PortfolioPerformanceCard: View {
    let chart: ChartData?
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Performance", subtitle: "Portfolio history from VisualizationEngine", icon: "waveform.path.ecg", tint: .cyan, state: state) {
            if let chart, !chart.points.isEmpty {
                Chart(chart.points) { point in
                    LineMark(x: .value("Date", point.label), y: .value("Value", point.value))
                        .foregroundStyle(.cyan.gradient)
                    AreaMark(x: .value("Date", point.label), y: .value("Value", point.value))
                        .foregroundStyle(.cyan.opacity(0.14).gradient)
                }
                .chartXAxis(.hidden)
                .chartYAxis(.hidden)
                .frame(height: 130)
                .accessibilityLabel("Portfolio performance chart")
            } else {
                EmptyStateCard(title: "Performance history is unavailable.", icon: "chart.line.uptrend.xyaxis")
            }
        }
    }
}
