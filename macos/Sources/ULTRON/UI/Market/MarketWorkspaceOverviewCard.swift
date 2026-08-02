import SwiftUI

public struct MarketWorkspaceOverviewCard: View {
    let indices: [MarketIndex]
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Market Overview", subtitle: "Connected index snapshot", icon: "chart.line.uptrend.xyaxis", tint: .green, state: state) {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(indices.prefix(3), id: \.symbol) { index in
                    HStack {
                        Text(index.name).font(.subheadline.weight(.semibold))
                        Spacer()
                        Text(index.changePercent.formatted(.percent))
                            .foregroundStyle(index.changePercent >= 0 ? .green : .red)
                    }
                }
            }
        }
    }
}
