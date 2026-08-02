import SwiftUI

public struct AIConversationView: View {
    let messages: [ConversationEntry]; let pendingQuestion: String?; let response: AdvisorResponse?
    public var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 16) {
                    if messages.isEmpty { EmptyAIView() }
                    ForEach(messages) { message in AIMessageBubble(message: message).id(message.id) }
                    if let pendingQuestion {
                        AIMessageBubble(message: ConversationEntry(role: .user, content: pendingQuestion))
                        AIThinkingCard()
                    }
                    if let response, messages.last?.role == .user {
                        AIWorkspaceInsightCard(response: response).id("ai-bottom")
                    }
                }
                .padding(24)
                .frame(maxWidth: 900, alignment: .leading)
                .frame(maxWidth: .infinity, alignment: .center)
            }
            .onChange(of: messages.count) { _, _ in
                withAnimation { proxy.scrollTo("ai-bottom", anchor: .bottom) }
            }
        }
    }
}
