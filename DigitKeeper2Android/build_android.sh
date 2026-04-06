#!/bin/bash
# ============================================================
#  DIGIT KEEPER 2 — Android APK Builder
#  Builds a .apk you can install on any Android device
#
#  Requirements (installed automatically):
#    - Docker Desktop (https://www.docker.com/products/docker-desktop)
#      OR
#    - Python 3, buildozer, Java 17, Android SDK
#
#  Easiest route:  Docker (handles all dependencies)
#  Usage:  chmod +x build_android.sh && ./build_android.sh
# ============================================================

set -e
APP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     DIGIT KEEPER 2 — Android APK Builder             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Method 1: Docker (recommended, easiest) ───────────────
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    echo "✅ Docker found — using containerised build (easiest!)"
    echo ""
    echo "🐳 Pulling buildozer Docker image..."
    docker pull kivy/buildozer 2>/dev/null || \
    docker pull ghcr.io/kivy/buildozer:latest

    echo ""
    echo "🔨 Building APK (this takes 10-20 min on first run)..."
    echo "   Subsequent builds are much faster."
    echo ""

    docker run --rm \
        -v "$APP_DIR":/home/user/hostcwd \
        kivy/buildozer \
        -v android debug

    APK_PATH=$(find "$APP_DIR/bin" -name "*.apk" 2>/dev/null | head -1)

    if [ -n "$APK_PATH" ]; then
        echo ""
        echo "╔══════════════════════════════════════════════════════╗"
        echo "║   ✅  APK BUILT SUCCESSFULLY!                         ║"
        echo "╚══════════════════════════════════════════════════════╝"
        echo ""
        echo "   APK: $APK_PATH"
        echo ""
        echo "   Install methods:"
        echo "   1. Email APK to yourself → open on Android"
        echo "   2. adb install '$APK_PATH'"
        echo "   3. Copy to phone via USB → install from Files app"
        echo ""
        open "$(dirname "$APK_PATH")" 2>/dev/null || true
    else
        echo "❌ APK not found after build. Check output above."
        exit 1
    fi

# ── Method 2: Native buildozer (Linux/Mac with Python) ────
elif command -v buildozer &>/dev/null; then
    echo "✅ buildozer found — native build"
    cd "$APP_DIR"
    buildozer -v android debug
    open bin/ 2>/dev/null || xdg-open bin/ 2>/dev/null || true

# ── Method 3: Install buildozer then build ────────────────
elif command -v pip3 &>/dev/null; then
    echo "📦 Installing buildozer..."
    pip3 install --user buildozer cython

    # Check Java
    if ! command -v java &>/dev/null; then
        echo ""
        echo "⚠️  Java not found. Install Java 17:"
        echo "   brew install openjdk@17"
        echo "   or download from https://adoptium.net"
        exit 1
    fi

    # Check Android SDK
    if [ -z "$ANDROID_HOME" ] && [ ! -d "$HOME/Library/Android/sdk" ]; then
        echo ""
        echo "⚠️  Android SDK not found."
        echo "   Buildozer will auto-download it on first run."
        echo "   This requires ~4GB of disk space."
        echo ""
    fi

    echo "🔨 Building APK..."
    cd "$APP_DIR"
    python3 -m buildozer -v android debug

    open bin/ 2>/dev/null || true

else
    echo "❌ No build tool found."
    echo ""
    echo "Choose one of these options:"
    echo ""
    echo "  OPTION A (Easiest) — Install Docker Desktop:"
    echo "  https://www.docker.com/products/docker-desktop"
    echo "  Then re-run this script."
    echo ""
    echo "  OPTION B — Install buildozer manually:"
    echo "  pip3 install buildozer cython"
    echo "  brew install openjdk@17"
    echo "  Then re-run this script."
    echo ""
    echo "  OPTION C — Use GitHub Actions (builds in the cloud):"
    echo "  See ANDROID_SETUP.md for instructions."
    exit 1
fi
