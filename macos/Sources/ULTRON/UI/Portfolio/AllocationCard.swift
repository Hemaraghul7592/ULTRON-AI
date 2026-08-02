import Charts
import SwiftUI

public struct PortfolioWorkspaceAllocationCard: View {
    let chart: ChartData?
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Allocation", subtitle: "Current holding values", icon: "chart.pie.fill", tint: .purple, state: state) {
            if let chart {
                HStack(spacing: 20) {
                    Chart(Array(chart.segments), id: \.label) { segment in
                        SectorMark(angle: .value("Value", segment.value), innerRadius: .ratio(0.58), angularInset: 2)
                            .foregroundStyle(by: .value("Holding", segment.label))
                    }
                    .chartLegend(.hidden)
                    .frame(width: 130, height: 130)
                    .accessibilityLabel("Portfolio allocation chart")

                    VStack(alignment: .leading, spacing: 7) {
                        ForEach(Array(chart.segments.prefix(5)), id: \.label) { segment in
                            HStack(spacing: 8) {
                                Circle().fill(.secondary).frame(width: 7, height: 7)
                                Text(segment.label).font(.caption)
                                Spacer()
                                Text(segment.value.formatted(.currency(code: "USD"))).font(.caption.weight(.semibold))
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }
}
