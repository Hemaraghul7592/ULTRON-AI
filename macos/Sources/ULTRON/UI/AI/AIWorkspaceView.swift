import AppKit
import SwiftUI

public struct AIWorkspaceView: View {
    @StateObject private var viewModel: AIWorkspaceViewModel
    public init(viewModel: AIWorkspaceViewModel) { _viewModel = StateObject(wrappedValue: viewModel) }
    public var body: some View {
        HStack(spacing: 0) {
            AISidebar(viewModel: viewModel)
            Divider()
            VStack(spacing: 0) {
                AIStatusView(state: viewModel.state)
                AIConversationView(messages: viewModel.messages, pendingQuestion: viewModel.pendingQuestion, response: viewModel.latestResponse)
                if !viewModel.recommendations.isEmpty {
                    AIRecommendationCard(recommendations: viewModel.recommendations)
                        .frame(maxWidth: 900)
                }
                if !viewModel.suggestions.isEmpty && viewModel.messages.isEmpty { AIPromptSuggestions(suggestions: viewModel.suggestions) { suggestion in Task { await viewModel.send(question: suggestion) } } }
                if !viewModel.messages.isEmpty {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 180), spacing: 8)], spacing: 8) {
                        ForEach(viewModel.actions, id: \.self) { action in
                            AIActionCard(action: action, detail: viewModel.action(action)) {
                                if action == .copySummary {
                                    NSPasteboard.general.clearContents()
                                    NSPasteboard.general.setString(viewModel.action(action), forType: .string)
                                } else {
                                    Task { await viewModel.send(question: action.rawValue) }
                                }
                            }
                        }
                    }
                    .frame(maxWidth: 900)
                }
                AIInputBar(input: $viewModel.input, isBusy: viewModel.state == .thinking || viewModel.state == .streamingReady, onSend: { Task { await viewModel.send() } }, onCancel: viewModel.cancel)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .background(Color.black.opacity(0.94))
        .task { await viewModel.loadWorkspace() }
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("ai.workspace")
    }
}

#if DEBUG
#Preview("AI Empty") { AIWorkspaceView(viewModel: AIPreviewFactory.make(state: .idle)).frame(width: 1200, height: 800) }
#Preview("AI Thinking") { AIWorkspaceView(viewModel: AIPreviewFactory.make(state: .thinking)).frame(width: 900, height: 650) }
#endif
