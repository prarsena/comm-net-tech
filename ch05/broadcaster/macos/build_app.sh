#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/build/CS240BroadcastListener.app"
CONTENTS_DIR="$APP_DIR/Contents"

if [[ "$(uname -s)" != "Darwin" ]]; then
    printf 'This app can only be built on macOS.\n' >&2
    exit 1
fi

if ! command -v xcrun >/dev/null 2>&1; then
    printf 'Install Xcode Command Line Tools to build this app.\n' >&2
    exit 127
fi

if [[ "$(sysctl -n hw.optional.arm64 2>/dev/null || true)" == "1" ]]; then
    MACHINE_ARCH=arm64
else
    MACHINE_ARCH="$(uname -m)"
fi

case "$MACHINE_ARCH" in
    arm64)
        TARGET_ARCH=arm64
        MINIMUM_OS_VERSION=11.0
        ;;
    x86_64)
        TARGET_ARCH=x86_64
        MINIMUM_OS_VERSION="${MACOSX_DEPLOYMENT_TARGET:-10.6}"
        ;;
    i386)
        if [[ "$(sysctl -n hw.optional.x86_64 2>/dev/null || true)" == "1" ]]; then
            TARGET_ARCH=x86_64
            MINIMUM_OS_VERSION="${MACOSX_DEPLOYMENT_TARGET:-10.6}"
        else
            printf 'This build currently supports 64-bit Intel Macs only.\n' >&2
            exit 1
        fi
        ;;
    *)
        printf 'Unsupported machine architecture: %s\n' "$MACHINE_ARCH" >&2
        exit 1
        ;;
esac

if [[ ! "$MINIMUM_OS_VERSION" =~ ^[0-9]+\.[0-9]+$ ]]; then
    printf 'Invalid MACOSX_DEPLOYMENT_TARGET: %s\n' "$MINIMUM_OS_VERSION" >&2
    exit 2
fi

if [[ "$TARGET_ARCH" == "arm64" ]] &&
    ! awk -v version="$MINIMUM_OS_VERSION" 'BEGIN { exit !(version >= 11.0) }'; then
    printf 'arm64 builds require macOS 11.0 or later.\n' >&2
    exit 2
fi

SDK_PATH="$(xcrun --sdk macosx --show-sdk-path)"
CLANG="$(xcrun --sdk macosx --find clang)"
mkdir -p "$CONTENTS_DIR/MacOS"
cp "$SCRIPT_DIR/Info.plist" "$CONTENTS_DIR/Info.plist"
/usr/libexec/PlistBuddy \
    -c "Set :LSMinimumSystemVersion $MINIMUM_OS_VERSION" \
    "$CONTENTS_DIR/Info.plist"

"$CLANG" \
    -arch "$TARGET_ARCH" \
    -fno-objc-arc \
    -fblocks \
    -Wall \
    -Wextra \
    -isysroot "$SDK_PATH" \
    -mmacosx-version-min="$MINIMUM_OS_VERSION" \
    "$SCRIPT_DIR/BroadcastListener.m" \
    -framework Cocoa \
    -o "$CONTENTS_DIR/MacOS/CS240BroadcastListener"

printf 'Built %s for %s (minimum macOS %s)\n' \
    "$APP_DIR" "$TARGET_ARCH" "$MINIMUM_OS_VERSION"
printf 'Launch it with: open "%s"\n' "$APP_DIR"
