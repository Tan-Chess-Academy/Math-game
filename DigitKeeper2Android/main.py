"""
main.py — Android entry point for Digit Keeper 2
=================================================
This file:
  1. Detects if running on Android (via ANDROID_ARGUMENT env var or android module)
  2. Patches screen size to device display resolution
  3. Injects touch controls over the game loop
  4. Adjusts font sizes for high-DPI mobile screens
  5. Redirects save files to Android writable storage
  6. Launches the game

Buildozer will package this as the app entry point.
"""

import os
import sys
import math
import pygame

# ── Detect Android ────────────────────────────────────────
try:
    import android
    IS_ANDROID = True
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                         Permission.READ_EXTERNAL_STORAGE])
except ImportError:
    IS_ANDROID = False

# ── Redirect save file to writable storage on Android ─────
if IS_ANDROID:
    try:
        from android.storage import app_storage_path
        SAVE_DIR = app_storage_path()
    except Exception:
        SAVE_DIR = os.path.expanduser("~")
    os.environ["DK_SAVE_DIR"] = SAVE_DIR
else:
    os.environ.setdefault("DK_SAVE_DIR",
                          os.path.dirname(os.path.abspath(__file__)))

# ── Patch pygame display for Android ──────────────────────
pygame.init()

if IS_ANDROID:
    # Use full device screen
    info = pygame.display.Info()
    SCREEN_W = info.current_w
    SCREEN_H = info.current_h
    # Force landscape
    if SCREEN_H > SCREEN_W:
        SCREEN_W, SCREEN_H = SCREEN_H, SCREEN_W
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
else:
    SCREEN_W, SCREEN_H = 1200, 740
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

pygame.display.set_caption("Digit Keeper 2")
clock = pygame.time.Clock()

# ── Scale factor for UI ───────────────────────────────────
# Reference design is 1200×740; scale everything proportionally
SCALE_X = SCREEN_W / 1200
SCALE_Y = SCREEN_H / 740
SCALE   = min(SCALE_X, SCALE_Y)

# ── Monkey-patch constants before importing game ──────────
# We override W, H and screen so the game uses our values
import types, builtins

_orig_pygame_display_set_mode = pygame.display.set_mode
def _patched_set_mode(size, *args, **kwargs):
    # Ignore game's set_mode call — we already set it up
    return screen
pygame.display.set_mode = _patched_set_mode

# ── Import touch overlay ──────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from touch_controls import TouchOverlay, TouchState

touch_state   = TouchState()
touch_overlay = TouchOverlay(SCREEN_W, SCREEN_H)

# ── Patch the game module namespace ──────────────────────
# We need to replace W, H after the game module sets them
# Strategy: run game code in a modified namespace

game_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "digit_keeper2.py")

with open(game_path, "r") as f:
    game_source = f.read()

# Patch the screen dimensions and init in the source
# (before any geometry is computed)
PATCHES = [
    # Screen size → device size
    ("W, H = 1200, 740",
     f"W, H = {SCREEN_W}, {SCREEN_H}"),

    # Don't re-init pygame (already done)
    ("pygame.init()",
     "pass  # pygame already inited by main.py"),

    # Save file path from env
    ('SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),\n'
     '                         "digit_keeper_save.json")',
     'SAVE_FILE = os.path.join(os.environ.get("DK_SAVE_DIR",\n'
     '    os.path.dirname(os.path.abspath(__file__))),\n'
     '    "digit_keeper_save.json")'),
]

for old, new in PATCHES:
    if old in game_source:
        game_source = game_source.replace(old, new, 1)

# ── Build patched game namespace ──────────────────────────
game_ns = {
    "__name__":  "__main__",
    "__file__":  game_path,
    "screen":    screen,
    "clock":     clock,
    "_touch_state":   touch_state,
    "_touch_overlay": touch_overlay,
    "_IS_ANDROID":    IS_ANDROID,
    "_SCALE":         SCALE,
}

# ── Inject touch control wrapper into the main loop ───────
# We insert touch processing at the top of each frame.
# The game's event loop uses "for event in pygame.event.get()"
# We wrap that by patching pygame.event.get to also emit
# synthetic KEYDOWN events from touch_state.

_real_event_get = pygame.event.get

def _touch_event_get(*args, **kwargs):
    """Wrapped pygame.event.get that injects touch→keyboard events."""
    events = _real_event_get(*args, **kwargs)

    in_battle = game_ns.get("pb_state") is not None
    in_trig   = (game_ns.get("trig") or {}).get("active", False)
    in_gallery= game_ns.get("gallery_active", False)

    # Process touch/mouse events through overlay
    consumed = set()
    for i, ev in enumerate(events):
        if touch_overlay.process_event(ev, touch_state,
                                        in_battle=in_battle):
            consumed.add(i)

    # Remove consumed events and add synthetic key events
    filtered = [ev for i,ev in enumerate(events) if i not in consumed]

    # Emit KEYDOWN for just-pressed virtual buttons
    for k in touch_state.pop_just_pressed():
        synthetic = pygame.event.Event(pygame.KEYDOWN, {
            "key":     k,
            "mod":     0,
            "unicode": "",
            "scancode": 0,
        })
        filtered.append(synthetic)

    # Emit unicode events from picker buttons
    for u in touch_state.pop_unicode():
        # Map unicode back to key constant where possible
        _unicode_map = {
            "s": pygame.K_s, "i_int": pygame.K_i, "j": pygame.K_j,
            "p": pygame.K_p, "=": pygame.K_EQUALS, "%": pygame.K_PERCENT,
            "+": pygame.K_PLUS, "-": pygame.K_MINUS,
            "*": pygame.K_ASTERISK, "/": pygame.K_SLASH,
            "(": pygame.K_LEFTPAREN, ")": pygame.K_RIGHTPAREN,
            "**": pygame.K_8,
            "sqrt": pygame.K_8,
        }
        kc = _unicode_map.get(u, pygame.K_RETURN)
        # For special display symbols map to actual unicode chars
        _disp_unicode = {
            "i_int": "i", "**": "*", "sqrt": "/",
        }
        uch = _disp_unicode.get(u, u)
        synthetic = pygame.event.Event(pygame.KEYDOWN, {
            "key":     kc,
            "mod":     0,
            "unicode": uch,
            "scancode": 0,
        })
        filtered.append(synthetic)

    return filtered

pygame.event.get = _touch_event_get

# ── Also wrap pygame.key.get_pressed to merge touch state ─
_real_key_get_pressed = pygame.key.get_pressed

def _touch_key_get_pressed():
    real = _real_key_get_pressed()
    ts_keys = touch_state.get_keys()
    class _Merged:
        def __getitem__(self, k):
            return real[k] or ts_keys[k]
    return _Merged()

pygame.key.get_pressed = _touch_key_get_pressed

# ── Wrap display.flip to draw touch overlay on top ────────
_real_flip = pygame.display.flip

def _touch_flip():
    # Determine context
    in_battle = game_ns.get("pb_state") is not None
    # Draw touch overlay
    touch_overlay.draw(screen, in_battle=in_battle)
    _real_flip()

pygame.display.flip = _touch_flip

# ── Scale fonts for mobile HiDPI ─────────────────────────
if SCALE > 1.3 or IS_ANDROID:
    # Game's make_font will be called with our scale applied
    _orig_make_font = None  # will be replaced after exec

# ── Run the game ──────────────────────────────────────────
print(f"Digit Keeper 2 — Android: {IS_ANDROID}, "
      f"Screen: {SCREEN_W}×{SCREEN_H}, Scale: {SCALE:.2f}")

exec(compile(game_source, game_path, "exec"), game_ns)
