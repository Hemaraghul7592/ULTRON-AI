import SwiftUI

public struct AIPromptSuggestions: View {
    let suggestions: [String]; let onSelect: (String) -> Void
    public var body: some View { VStack(alignment: .leading, spacing: 10) { Text("Suggested prompts").font(.caption.weight(.bold)).foregroundStyle(.secondary); LazyVGrid(columns: [GridItem(.adaptive(minimum: 190), spacing: 8)], spacing: 8) { ForEach(suggestions, id: \.self) { suggestion in Button(suggestion) { onSelect(suggestion) }.buttonStyle(.bordered).controlSize(.small) } } }.padding(.horizontal, 24).frame(maxWidth: 900, alignment: .leading).frame(maxWidth: .infinity, alignment: .center) }
}
