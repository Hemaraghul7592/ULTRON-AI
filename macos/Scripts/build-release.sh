#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

swift build -c release
mkdir -p "Release/artifacts"
cp ".build/release/ULTRON" "Release/artifacts/ULTRON"
codesign --verify --deep --strict "Release/artifacts/ULTRON" 2>/dev/null || {
  echo "Release executable is unsigned; configure ULTRON_CODE_SIGN_IDENTITY for signing." >&2
}
