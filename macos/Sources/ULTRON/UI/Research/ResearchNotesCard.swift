import SwiftUI

public struct ResearchNotesCard: View {
    @Binding var notes: String; let state: DashboardCardState; let onSave: () -> Void
    public var body: some View { DashboardCard(title: "Research Notes", subtitle: "Local notes prepared for future persistence", icon: "note.text", tint: .blue, state: state) { VStack(alignment: .leading, spacing: 8) { TextEditor(text: $notes).font(.caption).scrollContentBackground(.hidden).background(Color.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 8, style: .continuous)).frame(minHeight: 100).accessibilityIdentifier("research.notes"); HStack { Spacer(); Button("Save Notes", action: onSave).buttonStyle(.bordered).controlSize(.small) } } } }
}
