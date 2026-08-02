import Foundation

/// Shared defensive HTTP and decoding helpers for financial providers.
enum ProviderHTTP {
    static func makeURL(base: String, queryItems: [URLQueryItem] = []) throws -> URL {
        guard var components = URLComponents(string: base) else {
            throw FinancialError.invalidData("Invalid provider URL")
        }
        components.queryItems = queryItems.isEmpty ? components.queryItems : queryItems
        guard let url = components.url else {
            throw FinancialError.invalidData("Invalid provider URL components")
        }
        return url
    }

    static func data(from request: URLRequest, session: URLSession, provider: String) async throws -> Data {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch let error as URLError {
            throw FinancialError.networkFailure("\(provider): \(error.code.rawValue)")
        } catch {
            throw FinancialError.networkFailure("\(provider): \(error.localizedDescription)")
        }

        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            let status = (response as? HTTPURLResponse)?.statusCode.description ?? "non-HTTP response"
            throw FinancialError.invalidResponse("\(provider) returned HTTP \(status)")
        }
        guard !data.isEmpty else { throw FinancialError.emptyResponse(provider) }
        return data
    }

    static func decode<T: Decodable>(_ type: T.Type, data: Data, provider: String, decoder: JSONDecoder = JSONDecoder()) throws -> T {
        do {
            return try decoder.decode(type, from: data)
        } catch {
            throw FinancialError.decodingFailed("\(provider): \(error.localizedDescription)")
        }
    }
}
