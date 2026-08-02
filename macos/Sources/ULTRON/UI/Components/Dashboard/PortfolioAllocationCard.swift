import SwiftUI

public struct PortfolioAllocationCard: View {
    private let chart: ChartData?
    private let state: DashboardCardState

    public init(chart: ChartData?, state: DashboardCardState) {
        self.chart = chart
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "Portfolio Allocation", subtitle: "Current holdings", icon: "chart.pie.fill", tint: .purple, state: state) {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(Array(chart?.segments.prefix(5) ?? []), id: \.label) { segment in
                    HStack(spacing: 10) {
                        Circle()
                            .fill(color(for: segment))
                            .frame(width: 8, height: 8)
                        Text(segment.label)
                            .font(.subheadline)
                        Spacer()
                        Text(segment.value.formatted(.currency(code: "USD")))
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    private func color(for segment: SegmentData) -> Color {
        switch segment.color.lowercased() {
        case "blue": .blue
        case "green": .green
        case "orange": .orange
        case "red": .red
        default: .purple
        }
    }
}
