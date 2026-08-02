import SwiftUI

public struct EmptyStateCard: View {
    private let title: String
    private let icon: String
    private let tint: Color

    public init(title: String, icon: String, tint: Color = .secondary) {
        self.title = title
        self.icon = icon
        self.tint = tint
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(tint)
            Text(title)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(title)
    }
}
