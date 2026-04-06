[app]

# ── App identity ──────────────────────────────────────────
title = Digit Keeper 2
package.name = digitkeeper2
package.domain = com.digitkeeper
version = 2.0

# ── Source ────────────────────────────────────────────────
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = digit_keeper2.py,touch_controls.py,main.py

# ── Requirements ─────────────────────────────────────────
# pygame-ce is the recommended modern pygame for Android
requirements = python3,pygame-ce

# ── Orientation ──────────────────────────────────────────
orientation = landscape

# ── Display ──────────────────────────────────────────────
fullscreen = 1

# ── Entry point ──────────────────────────────────────────
entrypoint = main.py

# ── Android ──────────────────────────────────────────────
android.minapi = 24
android.targetapi = 33
android.sdk = 33
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE

# Architecture — build for both arm64 and arm for wide compatibility
android.archs = arm64-v8a,armeabi-v7a

# ── App icon ─────────────────────────────────────────────
# If you have icon.png (512×512) in the project folder, it will be used
# icon.filename = %(source.dir)s/icon.png

# ── Presplash (loading screen) ───────────────────────────
# presplash.filename = %(source.dir)s/presplash.png
presplash_color = #000000

# ── Build ────────────────────────────────────────────────
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
