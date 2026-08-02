import Foundation

public struct PortfolioPersistenceEnvelope: Codable, Sendable {
    public static let currentVersion = 1
    public let version: Int
    public let portfolios: [Portfolio]
    public let watchlists: [Watchlist]

    public init(version: Int = PortfolioPersistenceEnvelope.currentVersion, portfolios: [Portfolio], watchlists: [Watchlist]) {
        self.version = version
        self.portfolios = portfolios
        self.watchlists = watchlists
    }
}

/// Versioned, atomic file storage for portfolio state.
public actor FilePortfolioStorage: PortfolioStorage {
    public let fileURL: URL

    public init(fileURL: URL = FilePortfolioStorage.defaultURL()) {
        self.fileURL = fileURL
    }

    public func save<T: Codable & Sendable>(_ item: T, forKey key: String) async throws {
        let data = try JSONEncoder().encode(item)
        if let envelope = item as? PortfolioPersistenceEnvelope {
            guard envelope.version == PortfolioPersistenceEnvelope.currentVersion else { return }
            _ = try JSONDecoder().decode(PortfolioPersistenceEnvelope.self, from: data)
        }

        let directory = fileURL.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let temporaryURL = directory.appendingPathComponent(".\(fileURL.lastPathComponent).\(UUID().uuidString).tmp")
        do {
            try data.write(to: temporaryURL, options: [.atomic])
            if FileManager.default.fileExists(atPath: fileURL.path) {
                _ = try FileManager.default.replaceItemAt(fileURL, withItemAt: temporaryURL)
            } else {
                try FileManager.default.moveItem(at: temporaryURL, to: fileURL)
            }
        } catch {
            try? FileManager.default.removeItem(at: temporaryURL)
            throw error
        }
    }

    public func load<T: Codable & Sendable>(forKey key: String) async throws -> T? {
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return nil }
        do {
            let data = try Data(contentsOf: fileURL)
            guard !data.isEmpty else { return nil }
            let envelope = try JSONDecoder().decode(PortfolioPersistenceEnvelope.self, from: data)
            guard envelope.version == PortfolioPersistenceEnvelope.currentVersion else { return nil }
            return envelope as? T
        } catch {
            return nil
        }
    }

    public func remove(forKey key: String) async {
        try? FileManager.default.removeItem(at: fileURL)
    }

    public static func defaultURL() -> URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first ?? FileManager.default.temporaryDirectory
        return base.appendingPathComponent("ULTRON/Portfolios.json")
    }
}
