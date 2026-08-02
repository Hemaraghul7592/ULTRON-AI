import SwiftUI

public struct CompanyProfileCard: View {
    let profile: CompanyProfile?
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Company Profile", subtitle: "Identity and classification", icon: "building.2.fill", tint: .blue, state: state) {
            VStack(alignment: .leading, spacing: 9) {
                profileRow("Exchange", profile?.exchange)
                profileRow("Sector", profile?.sector)
                profileRow("Industry", profile?.industry)
                profileRow("Country", profile?.country)
                profileRow("Market Cap", profile?.marketCap == 0 ? nil : profile?.marketCap.formatted(.currency(code: profile?.currency ?? "USD")))
                profileRow("Currency", profile?.currency)
            }
        }
    }

    private func profileRow(_ label: String, _ value: String?) -> some View {
        HStack {
            Text(label).font(.caption).foregroundStyle(.secondary)
            Spacer()
            Text(value?.isEmpty == false ? value! : "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value?.isEmpty == false ? .primary : .tertiary)
        }
    }
}
