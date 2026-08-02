import SwiftUI

public struct MarketSearchBar: View {
    @Binding var query: String
    let onSubmit: () -> Void
    @FocusState private var focused: Bool

    public init(query: Binding<String>, onSubmit: @escaping () -> Void) {
        _query = query
        self.onSubmit = onSubmit
    }

    public var body: some View {
        HStack(spacing: 9) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)
            TextField("Search symbol or company name", text: $query)
                .textFieldStyle(.plain)
                .focused($focused)
                .onSubmit {
                    focused = false
                    onSubmit()
                }
                .accessibilityIdentifier("market.search")
            if !query.isEmpty {
                Button {
                    query = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
                .accessibilityLabel("Clear market search")
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 9)
        .background(Color.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 10, style: .continuous))
        .frame(maxWidth: 440)
    }
}
