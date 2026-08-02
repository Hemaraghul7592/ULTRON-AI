import SwiftUI

public struct ResearchExportCard: View {
    let onCopy: () -> Void; let onMarkdown: () -> Void; let onJSON: () -> Void
    public var body: some View { DashboardCard(title: "Export Research", subtitle: "Copy or serialize current report", icon: "square.and.arrow.up.fill", tint: .secondary, state: .loaded) { HStack(spacing: 8) { Button("Copy Summary", action: onCopy).buttonStyle(.bordered).controlSize(.small); Button("Markdown", action: onMarkdown).buttonStyle(.bordered).controlSize(.small); Button("JSON", action: onJSON).buttonStyle(.bordered).controlSize(.small) } } }
}
