/// A single frame in the container's resolution stack.
///
/// Each frame records which type is currently being resolved. The stack
/// is used for circular dependency detection — if a type appears twice
/// in the same resolution chain, a cycle exists.
///
/// `ResolutionFrame` stores structured metadata rather than a raw
/// `ObjectIdentifier`, enabling future extensions such as resolution
/// timing and lifetime tracking without changing the stack data type.
public struct ResolutionFrame: Sendable {

    // MARK: - Properties

    /// The type being resolved.
    public let typeIdentifier: ObjectIdentifier

    /// A human-readable name for the type.
    public let typeName: String

    // MARK: - Initialization

    /// Creates a frame for the given type.
    ///
    /// - Parameters:
    ///   - typeIdentifier: The `ObjectIdentifier` of the type being resolved.
    ///   - typeName: A human-readable name for diagnostics. Defaults to
    ///     the `ObjectIdentifier` description if not provided.
    public init(typeIdentifier: ObjectIdentifier, typeName: String? = nil) {
        self.typeIdentifier = typeIdentifier
        self.typeName = typeName ?? String(describing: typeIdentifier)
    }
}
