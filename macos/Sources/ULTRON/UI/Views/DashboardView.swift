import SwiftUI

/// Main dashboard showing portfolio summary, market data, alerts and AI insights.
public struct DashboardView: View {
    @State private var portfolioValue = 0.0
    @State private var marketSummary = "Loading..."

    public init() {}

    public var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                HStack(spacing: 12) {
                    StatCard(title: "Portfolio Value", value: "$\(String(format: "%.0f", portfolioValue))", icon: "briefcase", color: .blue)
                    StatCard(title: "Market Status", value: marketSummary, icon: "chart.line.uptrend.xyaxis", color: .green)
                    StatCard(title: "Active Alerts", value: "3", icon: "bell.badge", color: .orange)
                    StatCard(title: "AI Insights", value: "2 new", icon: "brain.head.profile", color: .purple)
                }
                .padding(.horizontal)

                HStack(alignment: .top, spacing: 16) {
                    VStack(alignment: .leading) {
                        Text("Recent Activity").font(.headline)
                        Divider()
                        RecentActivityRow(title: "Portfolio reviewed", detail: "2 recommendations", time: "5m ago")
                        RecentActivityRow(title: "Market update", detail: "NIFTY +1.2%", time: "15m ago")
                        RecentActivityRow(title: "SEBI filing", detail: "TCS Q4 Results", time: "1h ago")
                        RecentActivityRow(title: "Alert triggered", detail: "AAPL RSI > 70", time: "2h ago")
                    }
                    .frame(maxWidth: .infinity)

                    VStack(alignment: .leading) {
                        Text("AI Recommendations").font(.headline)
                        Divider()
                        RecommendationCard(symbol: "TCS", action: "Increase", reason: "Strong fundamentals, promoter buying", confidence: 82)
                        RecommendationCard(symbol: "INFY", action: "Hold", reason: "Fair valuation, steady growth", confidence: 65)
                    }
                    .frame(maxWidth: .infinity)
                }
                .padding(.horizontal)
            }
        }
    }
}

public struct StatCard: View {
    let title: String; let value: String; let icon: String; let color: Color
    public init(title: String, value: String, icon: String, color: Color) { self.title = title; self.value = value; self.icon = icon; self.color = color }
    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack { Image(systemName: icon).foregroundColor(color); Spacer() }
            Text(value).font(.title2).fontWeight(.bold)
            Text(title).font(.caption).foregroundColor(.secondary)
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 12).fill(.background).shadow(radius: 1))
    }
}

public struct RecentActivityRow: View {
    let title: String; let detail: String; let time: String
    public init(title: String, detail: String, time: String) { self.title = title; self.detail = detail; self.time = time }
    public var body: some View {
        HStack { VStack(alignment: .leading) { Text(title).font(.subheadline); Text(detail).font(.caption).foregroundColor(.secondary) }; Spacer(); Text(time).font(.caption).foregroundColor(.secondary) }
        .padding(.vertical, 4)
    }
}

public struct RecommendationCard: View {
    let symbol: String; let action: String; let reason: String; let confidence: Int
    public init(symbol: String, action: String, reason: String, confidence: Int) { self.symbol = symbol; self.action = action; self.reason = reason; self.confidence = confidence }
    public var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack { Text(symbol).font(.headline); Spacer(); Text("\(confidence)%").font(.caption).foregroundColor(.green) }
            Text(action).font(.subheadline).fontWeight(.semibold).foregroundColor(action == "Increase" ? .green : .orange)
            Text(reason).font(.caption).foregroundColor(.secondary)
        }
        .padding(10)
        .background(RoundedRectangle(cornerRadius: 8).fill(.background).shadow(radius: 0.5))
    }
}
