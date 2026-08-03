// swift-tools-version: 6.0

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
            exclude: ["Secrets"]
        ),
        .testTarget(
            name: "UnitTests",
            dependencies: ["ULTRON"],
            path: "Tests/UnitTests"
        ),
    ]
)
