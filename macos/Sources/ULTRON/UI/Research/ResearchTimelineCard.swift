import SwiftUI

public struct ResearchTimelineCard: View {
    let events: [ResearchTimelineEvent]; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Research Timeline", subtitle: "Chronological news and observations", icon: "timeline.selection", tint: .orange, state: state) { VStack(alignment: .leading, spacing: 10) { ForEach(events.prefix(6)) { event in HStack(alignment: .top, spacing: 10) { Circle().fill(.orange).frame(width: 7, height: 7).padding(.top, 5); VStack(alignment: .leading, spacing: 3) { Text(event.title).font(.caption.weight(.semibold)).lineLimit(2); Text("\(event.detail) | \(event.date.formatted(date: .abbreviated, time: .shortened))").font(.caption2).foregroundStyle(.secondary) } } } } } }
}
