/// The health status of a service provider.
public enum HealthStatus: String, Sendable, Codable {
    /// Provider is accepting requests and responding normally.
    case healthy

    /// Provider has some failures but is still accepting requests.
    case degraded

    /// Provider has exceeded its failure threshold and is being skipped.
    case unhealthy

    /// Provider is in its recovery cooldown period.
    case inCooldown
}
