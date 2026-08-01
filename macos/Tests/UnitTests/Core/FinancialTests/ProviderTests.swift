import Foundation
import Testing

@testable import ULTRON

// MARK: - Provider Tests

@MainActor
@Suite struct FinancialProviderTests {

    @Test("FinnhubProvider registers and health checks")
    func testFinnhubRegistration() async {
        let engine = FinancialEngine(config: .init(), logger: Logger(configuration: .init(minimumLevel: .error)))
        let provider = FinnhubProvider(apiKey: "test-key")
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.quotes, .companyProfile, .news, .ohlcv])
        #expect(engine.registeredProviderIDs().contains("finnhub"))
        #expect(engine.providers(for: .quotes).contains("finnhub"))
    }

    @Test("NewsAPIProvider registers and health checks")
    func testNewsAPIRegistration() async {
        let engine = FinancialEngine(config: .init(), logger: Logger(configuration: .init(minimumLevel: .error)))
        let provider = NewsAPIProvider(apiKey: "test-key")
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.news])
        #expect(engine.registeredProviderIDs().contains("newsapi"))
        #expect(engine.providers(for: .news).contains("newsapi"))
    }

    @Test("BinanceProvider registers without API key")
    func testBinanceRegistration() async {
        let engine = FinancialEngine(config: .init(), logger: Logger(configuration: .init(minimumLevel: .error)))
        let provider = BinanceProvider()
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.quotes, .ohlcv, .crypto])
        #expect(engine.registeredProviderIDs().contains("binance"))
        #expect(engine.providers(for: .quotes).contains("binance"))
        #expect(engine.providers(for: .crypto).contains("binance"))
    }

    @Test("OllamaProvider registers and health checks")
    func testOllamaRegistration() async {
        let engine = FinancialEngine(config: .init(), logger: Logger(configuration: .init(minimumLevel: .error)))
        let provider = OllamaProvider(endpoint: "http://localhost:11434")
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.technicals, .fundamentals])
        #expect(engine.registeredProviderIDs().contains("ollama"))
        #expect(engine.providers(for: .technicals).contains("ollama"))
    }

    @Test("OpenRouterProvider registers and health checks")
    func testOpenRouterRegistration() async {
        let engine = FinancialEngine(config: .init(), logger: Logger(configuration: .init(minimumLevel: .error)))
        let provider = OpenRouterProvider(apiKey: "test-key")
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.technicals, .fundamentals])
        #expect(engine.registeredProviderIDs().contains("openrouter"))
    }

    @Test("All built-in providers registered together")
    func testAllProvidersRegistered() async {
        let engine = FinancialEngine(config: .init(), logger: Logger(configuration: .init(minimumLevel: .error)))

        let finnhub = FinnhubProvider(apiKey: "test")
        let newsapi = NewsAPIProvider(apiKey: "test")
        let binance = BinanceProvider()
        let ollama = OllamaProvider()
        let openrouter = OpenRouterProvider(apiKey: "test")
        let marketaux = MarketauxProvider()
        let hackerearth = HackerEarthProvider()
        let rbi = RBIProvider()

        await engine.registerProvider(finnhub)
        engine.updateRegistry(for: finnhub, capabilities: [.quotes, .companyProfile, .news, .ohlcv])
        await engine.registerProvider(newsapi)
        engine.updateRegistry(for: newsapi, capabilities: [.news])
        await engine.registerProvider(binance)
        engine.updateRegistry(for: binance, capabilities: [.quotes, .ohlcv, .crypto])
        await engine.registerProvider(ollama)
        engine.updateRegistry(for: ollama, capabilities: [.technicals, .fundamentals])
        await engine.registerProvider(openrouter)
        engine.updateRegistry(for: openrouter, capabilities: [.technicals, .fundamentals])
        await engine.registerProvider(marketaux)
        await engine.registerProvider(hackerearth)
        await engine.registerProvider(rbi)

        let ids = engine.registeredProviderIDs()
        #expect(ids.contains("finnhub"))
        #expect(ids.contains("newsapi"))
        #expect(ids.contains("binance"))
        #expect(ids.contains("ollama"))
        #expect(ids.contains("openrouter"))
        #expect(ids.contains("marketaux"))
        #expect(ids.contains("hackerearth"))
        #expect(ids.contains("rbi"))
    }

    @Test("FinnhubProvider health reports unhealthy without key")
    func testFinnhubNoKey() async {
        let provider = FinnhubProvider(apiKey: "")
        let status = await provider.healthCheck()
        #expect(status == .unhealthy)
    }

    @Test("BinanceProvider health reports healthy")
    func testBinanceHealth() async {
        let provider = BinanceProvider()
        let status = await provider.healthCheck()
        #expect(status == .healthy)
    }

    @Test("OllamaProvider handles unavailable endpoint gracefully")
    func testOllamaUnavailable() async {
        let provider = OllamaProvider(endpoint: "http://0.0.0.0:1")
        let status = await provider.healthCheck()
        #expect(status == .unhealthy)
    }
}

// MARK: - APIConfiguration Tests

@Suite struct APIConfigurationTests {

    @Test("Shared instance is non-nil")
    func testSharedExists() {
        let config = APIConfiguration.shared
        _ = config.finnhubKey
        _ = config.binanceApiKey
        _ = config.ollamaEndpoint
    }

    @Test("Ollama endpoint has default")
    func testOllamaDefault() {
        let config = APIConfiguration.shared
        #expect(!config.ollamaEndpoint.isEmpty)
    }
}
