// swift-tools-version: 5.10

import PackageDescription

let package = Package(
    name: "ULTRON",
    platforms: [
        .macOS(.v14),
    ],
    products: [
        .executable(
            name: "ULTRON",
            targets: ["ULTRON"]
        ),
    ],
    targets: [
        .executableTarget(
            name: "ULTRON",
            path: "Sources/ULTRON",
            resources: [.process("Secrets")]
        ),
        .testTarget(
            name: "UnitTests",
            dependencies: ["ULTRON"],
            path: "Tests/UnitTests"
        ),
    ]
)
