# DIGIT KEEPER 2 — Android Build Guide

## Three ways to build the APK

---

## METHOD 1: Docker (Easiest — recommended)

No Android SDK setup needed. Docker handles everything.

### Steps

1. Install **Docker Desktop**:
   https://www.docker.com/products/docker-desktop

2. Start Docker Desktop (wait for it to fully load)

3. Open Terminal, go to this folder:
   ```bash
   cd /path/to/DigitKeeper2Android
   chmod +x build_android.sh
   ./build_android.sh
   ```

4. First build takes **15-25 minutes** (downloads Android SDK).
   Subsequent builds: **2-5 minutes**.

5. APK appears in `bin/digitkeeper2-2.0-debug.apk`

---

## METHOD 2: GitHub Actions (Build in the cloud — free)

No local setup at all. GitHub builds the APK for you.

### Steps

1. Create a free account at https://github.com

2. Create a new repository (e.g. `digit-keeper-2`)

3. Upload all files from this folder to the repo:
   ```bash
   git init
   git add .
   git commit -m "Digit Keeper 2 Android"
   git remote add origin https://github.com/YOUR_USER/digit-keeper-2.git
   git push -u origin main
   ```

4. Go to your repo on GitHub → **Actions** tab

5. The build starts automatically. Wait ~15 minutes.

6. Download the APK from the **Artifacts** section of the build.

---

## METHOD 3: Manual buildozer (Full control)

### Requirements

- macOS or Linux
- Python 3.10+
- Java 17
- ~10 GB free disk space

### Steps on Mac

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Java 17
brew install openjdk@17
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Install buildozer
pip3 install buildozer cython

# Build
cd /path/to/DigitKeeper2Android
buildozer android debug
```

---

## Installing the APK on Android

### Method A: Via USB (requires ADB)
```bash
# Install ADB
brew install android-platform-tools   # Mac
# or: https://developer.android.com/tools/releases/platform-tools

# Enable Developer Options on Android:
# Settings → About Phone → tap Build Number 7 times
# Settings → Developer Options → enable USB Debugging

adb install bin/digitkeeper2-2.0-debug.apk
```

### Method B: Email to yourself
- Email the .apk file to your Gmail
- Open on Android → tap to install
- May need: Settings → Security → Unknown Sources → ON

### Method C: Google Drive / Dropbox
- Upload APK to cloud storage
- Open on Android → download → install

---

## Touch Controls (Android)

The game adds a **virtual gamepad overlay**:

| Control | Action |
|---------|--------|
| ◀ ▶ (left) | Walk left/right |
| ▲ (left) | Jump |
| `0-9` button | Open digit picker |
| `+-*/` button | Open operator picker |
| `Σ∫i` button | Open special picker |
| `PLACE` | Place symbol (SPACE) |
| `PICK ⌫` | Pick up nearest |
| `EVAL ↵` | Evaluate expression |
| `CLR C` | Clear |
| `BAG B` | Open Bag |
| `GALL G` | Gallery |
| `TRIG T` | Trig mode |
| `🛡 SHIFT` | Raise shield (battle) |
| `FLICK F` | Flick attack (battle) |
| `SHOOT ▶` | Shoot (battle) |

**Tap any symbol in the picker strips** to pick it up instantly.

---

## File Structure

```
DigitKeeper2Android/
├── main.py              ← Android entry point (touch injection)
├── digit_keeper2.py     ← The full game
├── touch_controls.py    ← Virtual gamepad overlay
├── buildozer.spec       ← Build configuration
├── build_android.sh     ← One-command builder (Mac/Linux)
├── ANDROID_SETUP.md     ← This file
└── .github/
    └── workflows/
        └── build_apk.yml ← GitHub Actions CI build
```

---

## Troubleshooting

**"INSTALL_FAILED_UPDATE_INCOMPATIBLE"**
→ Uninstall the old version first: `adb uninstall com.digitkeeper.digitkeeper2`

**"App not installed"**
→ Enable Unknown Sources:
  Settings → Security → Install Unknown Apps → Files → Allow

**Black screen on launch**
→ Your device may need `armeabi-v7a` build.
  Edit `buildozer.spec`: change `android.archs` to `armeabi-v7a`

**Touch controls not responding**
→ The overlay is always on. If you have a keyboard connected,
  keyboard controls still work alongside touch.

**Save file location**
→ Android: saved to app private storage (auto-managed)
→ Back up by using Ctrl+S and Ctrl+L via the Bag menu
