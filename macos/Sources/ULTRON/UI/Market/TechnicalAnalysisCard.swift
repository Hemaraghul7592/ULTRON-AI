import SwiftUI

public struct TechnicalAnalysisCard: View {
    let technical: MarketTechnicalState
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Technical Analysis", subtitle: "TechnicalAnalysisEngine signals", icon: "waveform.path.ecg", tint: .orange, state: state) {
            VStack(alignment: .leading, spacing: 9) {
                analysisRow("Signal Summary", technical.signal?.strength.rawValue.capitalized)
                analysisRow("Confidence", technical.signal.map { $0.confidence.formatted(.percent) })
                analysisRow("RSI", technical.rsi?.values.last?.value.formatted(.number.precision(.fractionLength(2))))
                analysisRow("MACD", technical.macd?.macdLine.last?.value.formatted(.number.precision(.fractionLength(2))))
                analysisRow("Moving Average", technical.movingAverage?.values.last?.value.formatted(.number.precision(.fractionLength(2))))
                analysisRow("Bollinger Bands", technical.bollingerBands == nil ? nil : "Available")
                analysisRow("Trend", technical.signal?.strength.rawValue.capitalized)
                analysisRow("Support / Resistance", technical.patterns.isEmpty ? nil : "Patterns detected")
            }
        }
    }

    private func analysisRow(_ label: String, _ value: String?) -> some View {
        HStack {
            Text(label).font(.caption).foregroundStyle(.secondary)
            Spacer()
            Text(value ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary)
        }
    }
}
