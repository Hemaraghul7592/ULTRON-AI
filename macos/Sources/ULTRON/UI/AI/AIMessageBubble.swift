import SwiftUI

public struct AIMessageBubble: View {
    let message: ConversationEntry
    public var body: some View { HStack(alignment: .top, spacing: 10) { Image(systemName: message.role == .user ? "person.fill" : "sparkles").foregroundStyle(message.role == .user ? .blue : .pink).frame(width: 26); Text(message.content).font(.body).textSelection(.enabled); Spacer(minLength: 30) }.padding(14).background(message.role == .user ? Color.blue.opacity(0.1) : Color.white.opacity(0.045), in: RoundedRectangle(cornerRadius: 14, style: .continuous)).accessibilityElement(children: .combine).accessibilityLabel("\(message.role == .user ? "You" : "ULTRON"): \(message.content)") }
}
