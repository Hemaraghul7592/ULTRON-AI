/// A destination that forwards every log entry to multiple
/// child destinations.
///
/// Children are called sequentially in the order they were
/// registered. A failure in one child does not prevent the
/// remaining children from receiving the entry.
public struct CompositeDestination: LogDestination {

    // MARK: - Properties

    public let name = "Composite"

    /// The child destinations to forward entries to.
    private let children: [any LogDestination]

    // MARK: - Initialization

    /// Creates a composite destination.
    ///
    /// - Parameter children: The destinations to forward to.
    ///   Order is preserved for sequential delivery.
    public init(children: [any LogDestination]) {
        self.children = children
    }

    // MARK: - LogDestination

    public func write(_ entry: LogEntry) async {
        for child in children {
            await child.write(entry)
        }
    }
}
