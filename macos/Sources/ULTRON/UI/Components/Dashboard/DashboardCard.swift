import SwiftUI

public enum DashboardCardState: Equatable {
    case loading
    case loaded
    case empty
    case failed(String)
}

public struct DashboardCard<Content: View>: View {
    private let title: String
    private let subtitle: String?
    private let icon: String
    private let tint: Color
    private let state: DashboardCardState
    private let content: () -> Content

    @State private var isHovered = false

    public init(
        title: String,
        subtitle: String? = nil,
        icon: String,
        tint: Color = .accentColor,
        state: DashboardCardState,
        @ViewBuilder content: @escaping () -> Content
    ) {
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
        self.tint = tint
        self.state = state
        self.content = content
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            header
            Group {
                switch state {
                case .loading:
                    LoadingCard()
                case .loaded:
                    content()
                case .empty:
                    EmptyStateCard(title: "Nothing to show yet", icon: icon)
                case .failed(let message):
                    EmptyStateCard(title: message, icon: "exclamationmark.triangle", tint: .orange)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .transition(.opacity.combined(with: .scale(scale: 0.98)))
        }
        .padding(20)
        .background {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Color.white.opacity(isHovered ? 0.085 : 0.055))
                .overlay {
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color.white.opacity(isHovered ? 0.16 : 0.08), lineWidth: 1)
                }
        }
        .shadow(color: .black.opacity(isHovered ? 0.28 : 0.16), radius: isHovered ? 18 : 10, y: 8)
        .scaleEffect(isHovered ? 1.008 : 1)
        .onHover { hovering in
            withAnimation(.easeOut(duration: 0.18)) {
                isHovered = hovering
            }
        }
        .animation(.easeInOut(duration: 0.22), value: state)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("dashboard.card.\(title.lowercased().replacingOccurrences(of: " ", with: "."))")
    }

    private var header: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(tint)
                .frame(width: 30, height: 30)
                .background(tint.opacity(0.14), in: RoundedRectangle(cornerRadius: 9, style: .continuous))

            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.headline)
                    .foregroundStyle(.primary)
                if let subtitle {
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            Spacer(minLength: 0)
        }
    }
}
