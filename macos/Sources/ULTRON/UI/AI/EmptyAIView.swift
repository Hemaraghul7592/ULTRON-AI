import SwiftUI

public struct EmptyAIView: View { public var body: some View { VStack(spacing: 12) { Image(systemName: "sparkles").font(.largeTitle).foregroundStyle(.pink); Text("Ask ULTRON anything about your investments").font(.title3.weight(.semibold)); Text("Your portfolio, market, technical, fundamental, news, and conversation context will be considered automatically.").font(.subheadline).foregroundStyle(.secondary).multilineTextAlignment(.center).frame(maxWidth: 420) }.frame(maxWidth: .infinity).padding(.vertical, 120).accessibilityIdentifier("ai.empty") } }
