import SwiftUI

public struct ResearchSidebar: View {
    @Binding var searchQuery: String
    let favorites: Set<String>; let recent: [String]; let selectedSymbol: String?
    let onSearch: () -> Void; let onSelect: (String) -> Void
    public var body: some View {
        ScrollView { VStack(alignment: .leading, spacing: 20) { ResearchSearchBar(query: $searchQuery, onSubmit: onSearch); section("FAVORITES", Array(favorites).sorted()); section("RECENT", recent); Text("SAVED REPORTS").font(.system(size: 10, weight: .bold)).tracking(1.2).foregroundStyle(.tertiary); Text("Local reports will appear here.").font(.caption).foregroundStyle(.secondary) }.padding(16) }
            .frame(width: 220).background(Color.white.opacity(0.025)).accessibilityIdentifier("research.sidebar")
    }
    @ViewBuilder private func section(_ title: String, _ symbols: [String]) -> some View { VStack(alignment: .leading, spacing: 7) { Text(title).font(.system(size: 10, weight: .bold)).tracking(1.2).foregroundStyle(.tertiary); if symbols.isEmpty { Text("None yet").font(.caption).foregroundStyle(.secondary) } else { ForEach(symbols, id: \.self) { symbol in Button { onSelect(symbol) } label: { Label(symbol, systemImage: symbol == selectedSymbol ? "doc.text.magnifyingglass.fill" : "doc.text.magnifyingglass").foregroundStyle(symbol == selectedSymbol ? .blue : .primary).frame(maxWidth: .infinity, alignment: .leading) }.buttonStyle(.plain).accessibilityLabel("Open research for \(symbol)") } } } }
}
