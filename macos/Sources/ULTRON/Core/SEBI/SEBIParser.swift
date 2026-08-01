import Foundation

/// Parses and normalizes SEBI regulatory documents.
public enum SEBIParser {

    /// Extracts plain text from HTML content.
    public static func parseHTML(_ html: String) -> String {
        var text = html
        text = text.replacingOccurrences(of: "<[^>]+>", with: " ", options: .regularExpression)
        text = text.replacingOccurrences(of: "&amp;", with: "&")
        text = text.replacingOccurrences(of: "&lt;", with: "<")
        text = text.replacingOccurrences(of: "&gt;", with: ">")
        text = text.replacingOccurrences(of: "&quot;", with: "\"")
        text = text.replacingOccurrences(of: "&nbsp;", with: " ")
        text = text.replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
        return text.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// Normalizes text: lowercase, trim, collapse whitespace.
    public static func normalize(_ text: String) -> String {
        text.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
    }

    /// Detects duplicate filings by comparing normalized titles within a time window.
    public static func isDuplicate(_ new: SEBIFiling, existing: [SEBIFiling], windowSeconds: TimeInterval = 300) -> Bool {
        let key = "\(normalize(new.title)):\(new.company):\(new.category.rawValue)"
        return existing.contains { stored in
            let storedKey = "\(normalize(stored.title)):\(stored.company):\(stored.category.rawValue)"
            return storedKey == key && abs(new.date.timeIntervalSince(stored.date)) < windowSeconds
        }
    }

    /// Extracts keywords from text for search indexing.
    public static func extractKeywords(_ text: String) -> [String] {
        let cleaned = text.lowercased().replacingOccurrences(of: "[^a-z0-9\\s]", with: " ", options: .regularExpression)
        let words = cleaned.components(separatedBy: .whitespaces).filter { $0.count > 2 }
        return Array(Set(words)).sorted()
    }
}
