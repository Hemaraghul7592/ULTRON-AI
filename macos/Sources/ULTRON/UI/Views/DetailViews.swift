import SwiftUI

public struct MarketView: View {
    public init() {}
    public var body: some View {
        VStack(alignment: .leading) {
            Text("Markets").font(.largeTitle).fontWeight(.bold).padding()
            HStack(spacing: 12) {
                MarketIndexCard(name: "NIFTY 50", value: "24,500", change: "+1.2%", isUp: true)
                MarketIndexCard(name: "SENSEX", value: "80,200", change: "+0.9%", isUp: true)
                MarketIndexCard(name: "BANK NIFTY", value: "52,100", change: "-0.3%", isUp: false)
            }.padding(.horizontal)
            Spacer()
        }
    }
}

struct MarketIndexCard: View {
    let name: String; let value: String; let change: String; let isUp: Bool
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(name).font(.subheadline).foregroundColor(.secondary)
            Text(value).font(.title2).fontWeight(.bold)
            Text(change).font(.caption).foregroundColor(isUp ? .green : .red)
        }.padding().background(RoundedRectangle(cornerRadius: 10).fill(.background).shadow(radius: 1))
    }
}

public struct PortfolioView: View {
    public init() {}
    public var body: some View {
        VStack(alignment: .leading) { Text("Portfolio").font(.largeTitle).fontWeight(.bold).padding()
            List { StockRow(symbol: "AAPL", price: "180", change: "+2.3%", isUp: true); StockRow(symbol: "GOOGL", price: "140", change: "-0.5%", isUp: false); StockRow(symbol: "MSFT", price: "420", change: "+1.1%", isUp: true) }
        }
    }
}

public struct StockRow: View {
    let symbol: String; let price: String; let change: String; let isUp: Bool
    public init(symbol: String, price: String, change: String, isUp: Bool) { self.symbol = symbol; self.price = price; self.change = change; self.isUp = isUp }
    public var body: some View {
        HStack { Text(symbol).font(.headline); Spacer(); Text("$\(price)").font(.subheadline); Text(change).font(.caption).foregroundColor(isUp ? .green : .red).frame(width: 60, alignment: .trailing) }
    }
}

public struct WatchlistView: View {
    public init() {}
    public var body: some View { VStack { Text("Watchlists").font(.largeTitle).padding(); Spacer() } }
}

public struct ChartsView: View {
    public init() {}
    public var body: some View { VStack { Text("Charts").font(.largeTitle).padding(); Spacer() } }
}

public struct ResearchView: View {
    public init() {}
    public var body: some View { VStack { Text("Research").font(.largeTitle).padding(); Spacer() } }
}

public struct SEBIDetailView: View {
    public init() {}
    public var body: some View { VStack { Text("SEBI Filings").font(.largeTitle).padding(); Spacer() } }
}

public struct CopilotView: View {
    public init() {}
    public var body: some View { VStack { Text("Investment Copilot").font(.largeTitle).padding(); Spacer() } }
}

public struct AIChatView: View {
    @State private var messages: [ChatMessage] = [ChatMessage(role: "assistant", content: "Hello! I'm ULTRON's AI Financial Advisor. Ask me about your portfolio, stocks, or market analysis.")]
    @State private var input = ""
    public init() {}
    public var body: some View {
        VStack(spacing: 0) {
            ScrollView { VStack(alignment: .leading, spacing: 12) { ForEach(messages) { msg in HStack { if msg.role == "user" { Spacer() }; VStack(alignment: msg.role == "user" ? .trailing : .leading) { Text(msg.content).padding(10).background(msg.role == "user" ? Color.blue.opacity(0.2) : Color.gray.opacity(0.1)).cornerRadius(8) }; if msg.role == "assistant" { Spacer() } } }.padding(.horizontal) }.padding(.top) }
            HStack { TextField("Ask about your portfolio...", text: $input).textFieldStyle(.roundedBorder); Button("Send") { if !input.isEmpty { messages.append(ChatMessage(role: "user", content: input)); input = "" } }.buttonStyle(.borderedProminent) }.padding()
        }
    }
}

struct ChatMessage: Identifiable { let id = UUID(); let role: String; let content: String }

public struct AlertsView: View {
    public init() {}
    public var body: some View { VStack { Text("Alerts").font(.largeTitle).padding(); Spacer() } }
}

public struct SettingsView: View {
    public init() {}
    public var body: some View { VStack { Text("Settings").font(.largeTitle).padding(); Spacer() } }
}
