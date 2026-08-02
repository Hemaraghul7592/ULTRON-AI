# ULTRON Release Guide

## Release Gates

Run all platform checks before tagging:

```sh
cd backend && python -m pytest -q
cd ../macos && swift build && swift test && swift build -c release
cd ../android && ./gradlew clean test lint assembleRelease
```

The Android instrumentation suite requires an emulator or connected device:

```sh
cd android
./gradlew connectedCheck
```

## Backend Artifact

Build and validate the production image:

```sh
cd backend
docker build --tag ultron-backend:$GIT_SHA .
docker compose config
```

The image validates production environment variables before starting and runs as the `ultron` non-root user.

## macOS Artifact

The repository currently provides a SwiftPM release executable and signing placeholders:

```sh
cd macos
swift build -c release
./Scripts/build-release.sh
```

For a signed distribution, configure `ULTRON_CODE_SIGN_IDENTITY` and `ULTRON_DEVELOPMENT_TEAM`, then use the `Info.plist`, entitlements, and export options under `macos/Configuration` and `macos/Release` in the organization’s Xcode/archive pipeline.

## Android Artifact

Configure signing environment variables in CI, never in source control:

```text
ULTRON_KEYSTORE_FILE
ULTRON_KEYSTORE_PASSWORD
ULTRON_KEY_ALIAS
ULTRON_KEY_PASSWORD
ULTRON_BASE_URL
```

Then build:

```sh
cd android
./gradlew clean test lint assembleRelease
```

## Versioning

Update the backend version, macOS `MARKETING_VERSION` and `CURRENT_PROJECT_VERSION`, and Android `versionCode`/`versionName` together before tagging.

## Release Blockers

- macOS still requires an Xcode application/archive target and Apple signing credentials.
- Android still requires production keystore/Play App Signing configuration.
- Backend production secrets must be supplied by the deployment platform.
- Backend Ruff currently reports existing repository lint debt that must be resolved before a green CI release gate.
