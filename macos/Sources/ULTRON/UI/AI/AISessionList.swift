import SwiftUI

public struct AISessionList: View {
    let messages: [ConversationEntry]
    public var body: some View { VStack(alignment: .leading, spacing: 8) { Text("CONVERSATION").font(.system(size: 10, weight: .bold)).tracking(1.2).foregroundStyle(.tertiary); if messages.isEmpty { Text("New session").font(.caption).foregroundStyle(.secondary) } else { ForEach(messages.suffix(5)) { message in Text(message.content).font(.caption).lineLimit(2).foregroundStyle(.secondary) } } } }
}
