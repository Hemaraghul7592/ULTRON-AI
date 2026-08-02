import SwiftUI

public struct MarketStatusCard: View {
    let indices: [MarketIndex]
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Market Status", subtitle: "Connected market indices", icon: "globe.americas.fill", tint: .mint, state: state) {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(indices, id: \.symbol) { index in
                    HStack {
                        Text(index.name).font(.subheadline.weight(.semibold))
                        Spacer()
                        Text(index.value.formatted(.number.precision(.fractionLength(2))))
                        Text(index.changePercent.formatted(.percent))
                            .foregroundStyle(index.changePercent >= 0 ? .green : .red)
                    }
                }
            }
        }
    }
}
