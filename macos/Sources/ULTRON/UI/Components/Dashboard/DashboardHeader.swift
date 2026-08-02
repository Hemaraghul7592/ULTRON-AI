import SwiftUI

public struct DashboardHeader: View {
    private let marketStatus: DashboardMarketStatus
    private let lastUpdated: Date?
    private let isRefreshing: Bool
    private let onRefresh: () -> Void

    public init(
        marketStatus: DashboardMarketStatus,
        lastUpdated: Date?,
        isRefreshing: Bool,
        onRefresh: @escaping () -> Void
    ) {
        self.marketStatus = marketStatus
        self.lastUpdated = lastUpdated
        self.isRefreshing = isRefreshing
        self.onRefresh = onRefresh
    }

    public var body: some View {
        HStack(spacing: 16) {
            HStack(spacing: 12) {
                ZStack {
                    Circle()
                        .fill(.blue.gradient)
                    Image(systemName: "waveform.path.ecg")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundStyle(.white)
                }
                .frame(width: 38, height: 38)

                VStack(alignment: .leading, spacing: 2) {
                    Text("ULTRON")
                        .font(.system(size: 19, weight: .bold, design: .rounded))
                        .tracking(1.2)
                    Text("Financial command center")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer(minLength: 16)

            HStack(spacing: 14) {
                Label {
                    Text(marketStatus.rawValue)
                } icon: {
                    Circle()
                        .fill(marketStatus == .available ? .green : .secondary)
                        .frame(width: 7, height: 7)
                }
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)
                .accessibilityLabel("Market status: \(marketStatus.rawValue)")

                if let lastUpdated {
                    Text("Updated \(lastUpdated.formatted(date: .omitted, time: .shortened))")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }

                Button(action: onRefresh) {
                    Image(systemName: "arrow.clockwise")
                        .rotationEffect(.degrees(isRefreshing ? 360 : 0))
                        .animation(isRefreshing ? .linear(duration: 1).repeatForever(autoreverses: false) : .default, value: isRefreshing)
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                .disabled(isRefreshing)
                .help("Refresh dashboard")
                .accessibilityLabel("Refresh dashboard")

                Image(systemName: "person.crop.circle.fill")
                    .font(.title2)
                    .foregroundStyle(.secondary)
                    .accessibilityLabel("User profile")
            }
        }
        .padding(.horizontal, 4)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("dashboard.header")
    }
}
