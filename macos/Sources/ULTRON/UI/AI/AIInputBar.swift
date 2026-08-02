import SwiftUI

public struct AIInputBar: View {
    @Binding var input: String; let isBusy: Bool; let onSend: () -> Void; let onCancel: () -> Void; @FocusState private var focused: Bool
    public var body: some View { HStack(spacing: 10) { TextField("Ask ULTRON about your portfolio or the market...", text: $input, axis: .vertical).textFieldStyle(.plain).focused($focused).lineLimit(1...4).onSubmit { if !input.isEmpty { onSend() } }.accessibilityIdentifier("ai.input"); if isBusy { Button("Cancel", action: onCancel).buttonStyle(.bordered) } else { Button(action: onSend) { Image(systemName: "arrow.up.circle.fill").font(.title2) }.buttonStyle(.plain).disabled(input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty).accessibilityLabel("Send question") } }.padding(14).background(Color.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 14, style: .continuous)).padding(18) }
}
