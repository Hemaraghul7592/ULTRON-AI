import SwiftUI

public struct PortfolioHeader: View {
    let portfolio: Portfolio?
    let summary: PortfolioSummary?
    let lastUpdated: Date?
    let isRefreshing: Bool
    @Binding var searchText: String
    @Binding var sort: PortfolioHoldingSort
    @Binding var filter: PortfolioHoldingFilter
    let onRefresh: () -> Void
    @FocusState private var searchFocused: Bool

    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(portfolio?.name ?? "Portfolio")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                    Text(portfolio?.description.isEmpty == false ? portfolio?.description ?? "" : "Portfolio workspace")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if let lastUpdated {
                    Text("Updated \(lastUpdated.formatted(date: .omitted, time: .shortened))")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
                Button(action: onRefresh) {
                    Image(systemName: "arrow.clockwise")
                        .rotationEffect(.degrees(isRefreshing ? 360 : 0))
                        .animation(isRefreshing ? .linear(duration: 1).repeatForever(autoreverses: false) : .default, value: isRefreshing)
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                .disabled(isRefreshing)
                .accessibilityLabel("Refresh portfolio")
            }

            HStack(spacing: 10) {
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Search holdings", text: $searchText)
                        .textFieldStyle(.plain)
                        .focused($searchFocused)
                        .onSubmit { searchFocused = false }
                        .accessibilityIdentifier("portfolio.holdings.search")
                }
                .padding(.horizontal, 11)
                .padding(.vertical, 8)
                .background(Color.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 9, style: .continuous))
                .frame(maxWidth: 300)

                Picker("Filter", selection: $filter) {
                    ForEach(PortfolioHoldingFilter.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.menu)
                .accessibilityLabel("Filter holdings")

                Picker("Sort", selection: $sort) {
                    ForEach(PortfolioHoldingSort.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.menu)
                .accessibilityLabel("Sort holdings")
                Spacer()
            }
        }
        .accessibilityIdentifier("portfolio.header")
    }
}
