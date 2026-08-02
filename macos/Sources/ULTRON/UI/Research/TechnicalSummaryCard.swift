import SwiftUI

public struct TechnicalSummaryCard: View {
    let technical: MarketTechnicalState; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Technical Summary", subtitle: "TechnicalAnalysisEngine", icon: "waveform.path.ecg", tint: .cyan, state: state) { VStack(spacing: 9) { row("Trend", technical.signal?.strength.rawValue.capitalized); row("Signal", technical.signal?.reasons.first); row("RSI", technical.rsi?.values.last?.value.formatted(.number.precision(.fractionLength(2)))); row("MACD", technical.macd?.macdLine.last?.value.formatted(.number.precision(.fractionLength(2)))); row("Moving Average", technical.movingAverage?.values.last?.value.formatted(.number.precision(.fractionLength(2)))); row("Pattern Detection", technical.patterns.isEmpty ? nil : "Available"); row("Support / Resistance", technical.patterns.isEmpty ? nil : "Patterns detected") } } }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
}
