import SwiftUI

public struct LoadingCard: View {
    public init() {}

    public var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            RoundedRectangle(cornerRadius: 5, style: .continuous)
                .fill(Color.white.opacity(0.1))
                .frame(width: 150, height: 14)
            RoundedRectangle(cornerRadius: 5, style: .continuous)
                .fill(Color.white.opacity(0.07))
                .frame(maxWidth: .infinity)
            RoundedRectangle(cornerRadius: 5, style: .continuous)
                .fill(Color.white.opacity(0.07))
                .frame(width: 210, height: 12)
        }
        .redacted(reason: .placeholder)
        .accessibilityLabel("Loading")
    }
}
