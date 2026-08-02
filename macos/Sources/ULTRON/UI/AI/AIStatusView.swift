import SwiftUI

public struct AIStatusView: View {
    let state: AIWorkspaceState
    public var body: some View { HStack { Circle().fill(color).frame(width: 7, height: 7); Text(label).font(.caption).foregroundStyle(.secondary); Spacer() }.padding(.horizontal, 20).padding(.vertical, 9).background(Color.white.opacity(0.025)).accessibilityLabel("AI status: \(label)") }
    private var label: String { switch state { case .idle: "Ready"; case .loading: "Loading context"; case .thinking: "Thinking"; case .streamingReady: "Response ready"; case .completed: "Ready"; case .cancelled: "Cancelled"; case .failed: "Unavailable" } }
    private var color: Color { switch state { case .failed: .red; case .thinking, .streamingReady: .pink; case .cancelled: .orange; default: .green } }
}
