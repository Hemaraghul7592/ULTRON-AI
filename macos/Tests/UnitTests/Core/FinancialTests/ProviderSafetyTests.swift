import Foundation
import Testing

@testable import ULTRON

private final class ProviderURLProtocol: URLProtocol {
    enum Mode {
        case response(status: Int, body: Data)
        case failure(URLError.Code)
    }

    private static let lock = NSLock()
    private static var currentMode: Mode = .response(status: 200, body: Data())

    static func setMode(_ mode: Mode) {
        lock.lock(); defer { lock.unlock() }
        currentMode = mode
    }

    private static func mode() -> Mode {
        lock.lock(); defer { lock.unlock() }
        return currentMode
    }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        switch Self.mode() {
        case .response(let status, let body):
            let response = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: ["Content-Type": "application/json"])!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: body)
            client?.urlProtocolDidFinishLoading(self)
        case .failure(let code):
            client?.urlProtocol(self, didFailWithError: URLError(code))
        }
    }
    override func stopLoading() {}
}

@MainActor
@Suite(.serialized) struct ProviderSafetyTests {
    @Test("Finnhub non-2xx response becomes typed invalid response")
    func finnhub404() async {
        let provider = FinnhubProvider(apiKey: "test", session: session(mode: .response(status: 404, body: Data("{}".utf8))), baseURL: "http://provider.test/api/v1")
        await expectInvalidResponse { _ = try await provider.fetchQuote(symbol: "TEST") }
    }

    @Test("Finnhub malformed JSON becomes decoding failure")
    func finnhubMalformedJSON() async {
        let provider = FinnhubProvider(apiKey: "test", session: session(mode: .response(status: 200, body: Data("not-json".utf8))), baseURL: "http://provider.test/api/v1")
        await expectDecodingFailure { _ = try await provider.fetchQuote(symbol: "TEST") }
    }

    @Test("Finnhub missing candle fields becomes invalid response")
    func finnhubMissingFields() async {
        let body = Data("{\"s\":\"ok\",\"t\":[1],\"o\":[1]}".utf8)
        let provider = FinnhubProvider(apiKey: "test", session: session(mode: .response(status: 200, body: body)), baseURL: "http://provider.test/api/v1")
        await expectInvalidResponse { _ = try await provider.fetchOHLCV(symbol: "TEST", range: .oneDay) }
    }

    @Test("Binance invalid numeric data becomes invalid response")
    func binanceInvalidNumeric() async {
        let body = Data("{\"lastPrice\":\"bad\",\"priceChange\":\"1\",\"priceChangePercent\":\"1\",\"volume\":\"1\"}".utf8)
        let provider = BinanceProvider(session: session(mode: .response(status: 200, body: body)), baseURL: "http://provider.test")
        await expectInvalidResponse { _ = try await provider.fetchQuote(symbol: "TEST") }
    }

    @Test("Binance short kline becomes invalid response")
    func binanceShortKline() async {
        let provider = BinanceProvider(session: session(mode: .response(status: 200, body: Data("[[\"1\"]]".utf8))), baseURL: "http://provider.test")
        await expectInvalidResponse { _ = try await provider.fetchOHLCV(symbol: "TEST", range: .oneDay) }
    }

    @Test("NewsAPI HTTP 500 becomes invalid response")
    func news500() async {
        let provider = NewsAPIProvider(apiKey: "test", session: session(mode: .response(status: 500, body: Data("{}".utf8))), baseURL: "http://provider.test/v2")
        await expectInvalidResponse { _ = try await provider.fetchNews(symbols: ["TEST"]) }
    }

    @Test("NewsAPI empty body becomes empty response")
    func newsEmptyResponse() async {
        let provider = NewsAPIProvider(apiKey: "test", session: session(mode: .response(status: 200, body: Data())), baseURL: "http://provider.test/v2")
        await expectEmptyResponse { _ = try await provider.fetchNews(symbols: ["TEST"]) }
    }

    @Test("RBI malformed JSON becomes decoding failure")
    func rbiMalformedJSON() async {
        let provider = RBIProvider(endpoint: "http://provider.test", session: session(mode: .response(status: 200, body: Data("[]".utf8))) )
        await expectDecodingFailure { _ = try await provider.fetchCPI() }
    }

    @Test("Network failure becomes typed network failure")
    func networkFailure() async {
        let provider = FinnhubProvider(apiKey: "test", session: session(mode: .failure(.cannotConnectToHost)), baseURL: "http://provider.test/api/v1")
        await expectNetworkFailure { _ = try await provider.fetchQuote(symbol: "TEST") }
    }

    @Test("Timeout becomes typed network failure")
    func timeout() async {
        let provider = FinnhubProvider(apiKey: "test", session: session(mode: .failure(.timedOut)), baseURL: "http://provider.test/api/v1")
        await expectNetworkFailure { _ = try await provider.fetchQuote(symbol: "TEST") }
    }

    private func session(mode: ProviderURLProtocol.Mode) -> URLSession {
        ProviderURLProtocol.setMode(mode)
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [ProviderURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    private func expectInvalidResponse(_ operation: () async throws -> Void) async {
        do { try await operation(); Issue.record("Expected invalid response") }
        catch let error as FinancialError { if case .invalidResponse = error {} else { Issue.record("Unexpected error: \(error)") } }
        catch { Issue.record("Unexpected error: \(error)") }
    }

    private func expectDecodingFailure(_ operation: () async throws -> Void) async {
        do { try await operation(); Issue.record("Expected decoding failure") }
        catch let error as FinancialError { if case .decodingFailed = error {} else { Issue.record("Unexpected error: \(error)") } }
        catch { Issue.record("Unexpected error: \(error)") }
    }

    private func expectEmptyResponse(_ operation: () async throws -> Void) async {
        do { try await operation(); Issue.record("Expected empty response") }
        catch let error as FinancialError { if case .emptyResponse = error {} else { Issue.record("Unexpected error: \(error)") } }
        catch { Issue.record("Unexpected error: \(error)") }
    }

    private func expectNetworkFailure(_ operation: () async throws -> Void) async {
        do { try await operation(); Issue.record("Expected network failure") }
        catch let error as FinancialError { if case .networkFailure = error {} else { Issue.record("Unexpected error: \(error)") } }
        catch { Issue.record("Unexpected error: \(error)") }
    }
}
