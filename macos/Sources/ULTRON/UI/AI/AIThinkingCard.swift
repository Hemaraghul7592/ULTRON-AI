import SwiftUI

public struct AIThinkingCard: View { public var body: some View { HStack(spacing: 10) { ProgressView().controlSize(.small); Text("ULTRON is reviewing your context...").font(.subheadline).foregroundStyle(.secondary) }.padding(14).background(Color.pink.opacity(0.08), in: RoundedRectangle(cornerRadius: 14, style: .continuous)).accessibilityLabel("ULTRON is thinking") } }
