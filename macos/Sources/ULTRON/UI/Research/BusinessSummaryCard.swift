import SwiftUI

public struct BusinessSummaryCard: View {
    let company: CompanyProfile?; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Business Overview", subtitle: "Company classification", icon: "briefcase.fill", tint: .indigo, state: state) { VStack(alignment: .leading, spacing: 10) { Text("Description").font(.caption.weight(.bold)).foregroundStyle(.secondary); Text("Business description is unavailable from current provider models.").font(.subheadline).foregroundStyle(.secondary); row("Business model", nil); row("Industry", company?.industry); row("Sector", company?.sector); row("Listing exchange", company?.exchange); row("Country", company?.country) } } }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value?.isEmpty == false ? value! : "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil || value!.isEmpty ? .tertiary : .primary) } }
}
