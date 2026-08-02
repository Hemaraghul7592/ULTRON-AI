import SwiftUI

public struct AIActionCard: View {
    let action: AIAction; let detail: String; let onAction: () -> Void
    public var body: some View { Button(action: onAction) { HStack { Image(systemName: icon).foregroundStyle(.blue); VStack(alignment: .leading) { Text(action.rawValue).font(.caption.weight(.semibold)); Text(detail).font(.caption2).foregroundStyle(.secondary).lineLimit(1) }; Spacer(); Image(systemName: "chevron.right").font(.caption).foregroundStyle(.tertiary) }.padding(12).background(Color.white.opacity(0.05), in: RoundedRectangle(cornerRadius: 12, style: .continuous)) }.buttonStyle(.plain).accessibilityLabel(action.rawValue) }
    private var icon: String { switch action { case .researchCompany: "doc.text.magnifyingglass"; case .openPortfolio: "briefcase"; case .showTechnicals: "waveform.path.ecg"; case .openFundamentals: "building.columns"; case .createAlert: "bell"; case .addWatchlist: "eye"; case .copySummary: "doc.on.doc" } }
}
