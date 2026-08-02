import SwiftUI

public struct CompanySnapshotCard: View {
    let company: CompanyProfile?; let quote: Quote?; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Company Snapshot", subtitle: "FinancialEngine source data", icon: "building.2.fill", tint: .blue, state: state) { VStack(alignment: .leading, spacing: 8) { row("Name", company?.name); row("Ticker", company?.symbol); row("Exchange", company?.exchange); row("Sector", company?.sector); row("Industry", company?.industry); row("Latest Price", quote?.price.formatted(.currency(code: quote?.currency ?? "USD"))); row("Market Cap", company?.marketCap == 0 ? nil : company?.marketCap.formatted(.currency(code: company?.currency ?? "USD"))); row("Country", company?.country); row("Currency", company?.currency) } } }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value?.isEmpty == false ? value! : "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value?.isEmpty == false ? .primary : .tertiary) } }
}
