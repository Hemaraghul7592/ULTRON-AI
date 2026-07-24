/// An error that occurs during dependency container operations.
///
/// All errors include enough context to diagnose the issue without
/// exposing internal implementation details. The `description` property
/// produces human-readable messages suitable for logging and debugging.
public enum ContainerError: Error, CustomStringConvertible {

    /// The requested type was never registered with the container.
    case notRegistered(typeName: String)

    /// A circular dependency was detected during resolution.
    /// - Parameter chain: The full resolution chain showing the cycle.
    case circularDependency(chain: [ResolutionFrame])

    /// The factory closure threw an error during service construction.
    case factoryFailed(typeName: String, underlying: any Error)

    // MARK: - CustomStringConvertible

    public var description: String {
        switch self {
        case .notRegistered(let typeName):
            return "Type '\(typeName)' is not registered with the container."
        case .circularDependency(let chain):
            if chain.isEmpty { return "Circular dependency detected." }
            var lines = ["Circular dependency detected:"]
            lines.append("  \(chain[0].typeName)")
            for frame in chain.dropFirst() {
                lines.append("  ↓")
                lines.append("  \(frame.typeName)")
            }
            return lines.joined(separator: "\n")
        case .factoryFailed(let typeName, let error):
            return "Factory for '\(typeName)' failed: \(error)."
        }
    }
}
