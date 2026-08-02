import SwiftUI

public struct AISidebar: View {
    @ObservedObject var viewModel: AIWorkspaceViewModel
    public var body: some View { ScrollView { VStack(alignment: .leading, spacing: 18) { HStack { Image(systemName: "sparkles").foregroundStyle(.pink); Text("AI Copilot").font(.headline); Spacer() }; AISessionList(messages: viewModel.messages); AIContextCard(context: viewModel.context); Button("Clear conversation") { Task { await viewModel.clearConversation() } }.buttonStyle(.bordered).controlSize(.small).accessibilityLabel("Clear conversation") }.padding(16) }.frame(width: 260).background(Color.white.opacity(0.025)).accessibilityIdentifier("ai.sidebar") }
}
