import SwiftUI

public struct AIHistoryView: View {
    let messages: [ConversationEntry]
    public var body: some View { List(messages) { message in VStack(alignment: .leading) { Text(message.role == .user ? "You" : "ULTRON").font(.caption.weight(.bold)); Text(message.content).font(.caption) } } }
}
