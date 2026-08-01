import Foundation

/// The application composition root.
///
/// This is the only place where application services are constructed and
/// registered. Feature implementations remain unaware of the container.
@MainActor
public final class ApplicationCompositionRoot {

    public let container: DependencyContainer

    public init() {
        self.container = DependencyContainer()
        registerConfiguration()
        registerLogging()
        registerRepositories()
        registerCaches()
        registerProviders()
        registerAIProviders()
        registerEngines()
    }

    public init(container: DependencyContainer) {
        self.container = container
        registerConfiguration()
        registerLogging()
        registerRepositories()
        registerCaches()
        registerProviders()
        registerAIProviders()
        registerEngines()
    }

    /// Installs the provider startup and shutdown hook on the application's
    /// lifecycle sequences.
    public func registerLifecycleHooks(
        startup: StartupSequence,
        shutdown: ShutdownSequence
    ) {
        let hook = ProviderLifecycleHook(container: container)
        startup.register(hook)
        shutdown.register(hook)
    }

    private func registerConfiguration() {
        container.register(Configuration.self) { _ in Configuration() }
        container.register(BuildConfiguration.self) { _ in BuildConfiguration.current }
        container.register(APIConfiguration.self) { _ in APIConfiguration.shared }
        container.register(FinancialConfig.self) { _ in
            FinancialConfig(
                quoteProviderPriority: ["finnhub", "binance"],
                ohlcvProviderPriority: ["finnhub", "binance"],
                companyProviderPriority: ["finnhub"]
            )
        }
        container.register(TAConfig.self) { _ in .default }
        container.register(FAConfig.self) { _ in .default }
    }

    private func registerLogging() {
        container.register(LoggerConfiguration.self) { _ in
            let subsystem = Configuration.bundleIdentifier
            return LoggerConfiguration(
                minimumLevel: Configuration.isDebugBuild ? .debug : .info,
                subsystem: subsystem,
                destinations: [ConsoleDestination(subsystem: subsystem)],
                captureSourceLocation: Configuration.isDebugBuild
            )
        }
        container.register(Logger.self) { resolver in
            let configuration = try await resolver.resolve(LoggerConfiguration.self)
            return Logger(configuration: configuration)
        }
    }

    private func registerRepositories() {
        container.register(SEBIRepository.self) { _ in SEBIRepository() }
        container.register(InMemoryStorage.self) { _ in InMemoryStorage() }
        container.register(InMemoryAlertStorage.self) { _ in InMemoryAlertStorage() }
        container.register(AlertManager.self) { _ in AlertManager() }
    }

    private func registerCaches() {
        container.register(FinancialCache<String, Quote>.self) { _ in
            FinancialCache<String, Quote>(defaultTTL: 60)
        }
        container.register(FinancialCache<String, [OHLCV]>.self) { _ in
            FinancialCache<String, [OHLCV]>(defaultTTL: 3600)
        }
        container.register(FinancialCache<String, CompanyProfile>.self) { _ in
            FinancialCache<String, CompanyProfile>(defaultTTL: 86400)
        }
        container.register(IndicatorCache.self) { _ in IndicatorCache() }
    }

    private func registerProviders() {
        container.register(FinnhubProvider.self) { _ in FinnhubProvider() }
        container.register(NewsAPIProvider.self) { _ in NewsAPIProvider() }
        container.register(MarketauxProvider.self) { _ in MarketauxProvider() }
        container.register(BinanceProvider.self) { _ in BinanceProvider() }
        container.register(RBIProvider.self) { _ in RBIProvider() }
        container.register(OllamaProvider.self) { _ in OllamaProvider() }
        container.register(HackerEarthProvider.self) { _ in HackerEarthProvider() }
        container.register(OpenRouterProvider.self) { _ in OpenRouterProvider() }
        container.register(SEBIProvider.self) { _ in SEBIProvider() }

        container.register([any ServiceProvider].self) { resolver in
            [
                try await resolver.resolve(FinnhubProvider.self),
                try await resolver.resolve(NewsAPIProvider.self),
                try await resolver.resolve(MarketauxProvider.self),
                try await resolver.resolve(BinanceProvider.self),
                try await resolver.resolve(RBIProvider.self),
                try await resolver.resolve(OllamaProvider.self),
                try await resolver.resolve(HackerEarthProvider.self),
                try await resolver.resolve(OpenRouterProvider.self),
                try await resolver.resolve(SEBIProvider.self)
            ]
        }
    }

    private func registerAIProviders() {
        container.register(OpenRouterAdapter.self) { _ in OpenRouterAdapter() }
        container.register(OllamaAdapter.self) { _ in OllamaAdapter() }
        container.register([any LLMProvider].self) { resolver in
            [
                try await resolver.resolve(OpenRouterAdapter.self),
                try await resolver.resolve(OllamaAdapter.self)
            ]
        }
    }

    private func registerEngines() {
        container.register(FinancialEngine.self) { resolver in
            FinancialEngine(
                config: try await resolver.resolve(FinancialConfig.self),
                logger: try await resolver.resolve(Logger.self)
            )
        }
        container.register(TechnicalAnalysisEngine.self) { resolver in
            TechnicalAnalysisEngine(config: try await resolver.resolve(TAConfig.self))
        }
        container.register(FundamentalAnalysisEngine.self) { resolver in
            FundamentalAnalysisEngine(config: try await resolver.resolve(FAConfig.self))
        }
        container.register(PortfolioEngine.self) { resolver in
            PortfolioEngine(
                storage: try await resolver.resolve(InMemoryStorage.self),
                logger: try await resolver.resolve(Logger.self)
            )
        }
        container.register(AIAdvisorEngine.self) { resolver in
            let primary = try await resolver.resolve(OpenRouterAdapter.self)
            let fallback = try await resolver.resolve(OllamaAdapter.self)
            return AIAdvisorEngine(
                primary: primary,
                fallback: fallback,
                logger: try await resolver.resolve(Logger.self)
            )
        }
        container.register(VisualizationEngine.self) { resolver in
            VisualizationEngine(logger: try await resolver.resolve(Logger.self))
        }
        container.register(AlertEngine.self) { resolver in
            AlertEngine(
                manager: try await resolver.resolve(AlertManager.self),
                storage: try await resolver.resolve(InMemoryAlertStorage.self),
                logger: try await resolver.resolve(Logger.self)
            )
        }
        container.register(SEBIEngine.self) { resolver in
            SEBIEngine(logger: try await resolver.resolve(Logger.self))
        }
        container.register(InvestmentCopilotEngine.self) { resolver in
            InvestmentCopilotEngine(logger: try await resolver.resolve(Logger.self))
        }
        container.register(ServiceOrchestrator<FinnhubProvider>.self) { resolver in
            let orchestrator = ServiceOrchestrator<FinnhubProvider>(
                config: OrchestratorConfig(category: .custom),
                logger: try await resolver.resolve(Logger.self)
            )
            let provider = try await resolver.resolve(FinnhubProvider.self)
            orchestrator.register(provider, configuration: ProviderConfig(providerID: provider.providerID))
            return orchestrator
        }
    }
}

@MainActor
private struct ProviderLifecycleHook: LifecycleHook {
    let phase: StartupPhase = .dependencyInjection
    let priority = 10
    let label = "External Providers"

    private let container: DependencyContainer

    init(container: DependencyContainer) { self.container = container }

    func onStartup() async throws {
        let resolver = ContainerResolver(container: container)
        let providers = try await resolver.resolve([any ServiceProvider].self)
        let logger = try await resolver.resolve(Logger.self)
        for provider in providers {
            try await provider.initialize()
            let status = await provider.healthCheck()
            let metadata = [
                "provider": provider.providerID,
                "status": status.rawValue
            ]
            if status == .healthy {
                await logger.info("Provider startup completed", metadata: metadata)
            } else {
                await logger.warning("Provider startup completed", metadata: metadata)
            }
        }
    }

    func onShutdown() async {
        let resolver = ContainerResolver(container: container)
        guard let providers = try? await resolver.resolve([any ServiceProvider].self) else { return }
        for provider in providers.reversed() {
            await provider.shutdown()
        }
    }
}
