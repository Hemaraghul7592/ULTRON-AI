import SwiftUI

public struct ResearchSearchBar: View {
    @Binding var query: String; let onSubmit: () -> Void; @FocusState private var focused: Bool
    public init(query: Binding<String>, onSubmit: @escaping () -> Void) { _query = query; self.onSubmit = onSubmit }
    public var body: some View { HStack { Image(systemName: "magnifyingglass").foregroundStyle(.secondary); TextField("Search company or symbol", text: $query).textFieldStyle(.plain).focused($focused).onSubmit { focused = false; onSubmit() }.accessibilityIdentifier("research.search"); if !query.isEmpty { Button { query = "" } label: { Image(systemName: "xmark.circle.fill") }.buttonStyle(.plain).accessibilityLabel("Clear research search") } }.padding(10).background(Color.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 10, style: .continuous)).frame(maxWidth: 440) }
}
