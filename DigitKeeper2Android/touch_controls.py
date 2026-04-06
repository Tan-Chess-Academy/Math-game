"""
touch_controls.py — Virtual gamepad overlay for Digit Keeper 2 on Android.

Provides:
  - TouchState   : singleton that tracks virtual button states
  - TouchOverlay : draws the on-screen controls
  - inject_touch_events() : call each frame to translate touches → key state

Usage (injected at top of main loop):
    from touch_controls import TouchState, TouchOverlay, inject_touch_events
    overlay = TouchOverlay(W, H)
    ts = TouchState()

    # In event loop:
    inject_touch_events(ts, events)

    # In update:
    keys = ts.get_keys()    # drop-in replacement for pygame.key.get_pressed()
"""

import pygame
import math


# ── Colour palette ─────────────────────────────────────────
_BTN_BG    = (30,  30,  50,  160)
_BTN_ACT   = (80, 140, 200,  200)
_BTN_BDR   = (80,  80, 120,  200)
_BTN_TXT   = (200, 220, 255)
_DPAD_BG   = (20,  20,  40,  140)
_ORANGE    = (255, 140,  28,  200)


class _VButton:
    """A single circular or rectangular virtual button."""
    def __init__(self, x, y, w, h, label, key,
                 shape="rect", color=_BTN_BG):
        self.rect  = pygame.Rect(x, y, w, h)
        self.cx    = x + w // 2
        self.cy    = y + h // 2
        self.label = label
        self.key   = key          # pygame key constant this maps to
        self.shape = shape        # "rect" | "circle"
        self.color = color
        self.held  = False        # is finger currently on this?
        self._fid  = None         # finger id holding this

    def contains(self, fx, fy):
        if self.shape == "circle":
            r = min(self.rect.w, self.rect.h) // 2
            return math.hypot(fx - self.cx, fy - self.cy) <= r
        return self.rect.collidepoint(fx, fy)

    def draw(self, surf, font_sm, font_xs):
        alpha = 220 if self.held else 160
        col   = _BTN_ACT if self.held else self.color

        s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        if self.shape == "circle":
            r = min(self.rect.w, self.rect.h) // 2
            pygame.draw.circle(s, (*col[:3], alpha),
                               (self.rect.w//2, self.rect.h//2), r)
            pygame.draw.circle(s, (*_BTN_BDR[:3], alpha),
                               (self.rect.w//2, self.rect.h//2), r, 2)
        else:
            pygame.draw.rect(s, (*col[:3], alpha),
                             (0, 0, self.rect.w, self.rect.h),
                             border_radius=10)
            pygame.draw.rect(s, (*_BTN_BDR[:3], alpha),
                             (0, 0, self.rect.w, self.rect.h),
                             2, border_radius=10)
        surf.blit(s, self.rect.topleft)

        # Label
        font = font_sm if len(self.label) <= 3 else font_xs
        ls = font.render(self.label, True, _BTN_TXT)
        surf.blit(ls, (self.cx - ls.get_width()//2,
                       self.cy - ls.get_height()//2))


class TouchState:
    """Tracks virtual key states from touch input."""

    def __init__(self):
        self._held  = set()   # set of pygame.K_* constants currently pressed
        self._just  = set()   # pressed this frame (for KEYDOWN events)
        self._unicode_queue = []  # unicode chars queued (for text input buttons)

    def press(self, key, unicode_char=None):
        if key not in self._held:
            self._just.add(key)
        self._held.add(key)
        if unicode_char:
            self._unicode_queue.append(unicode_char)

    def release(self, key):
        self._held.discard(key)
        self._just.discard(key)

    def is_held(self, key):
        return key in self._held

    def pop_just_pressed(self):
        j = list(self._just)
        self._just.clear()
        return j

    def pop_unicode(self):
        u = list(self._unicode_queue)
        self._unicode_queue.clear()
        return u

    def get_keys(self):
        """Return a dict-like object usable as pygame.key.get_pressed()."""
        held = self._held
        class _FakeKeys:
            def __getitem__(self, k):
                return k in held
        return _FakeKeys()


class TouchOverlay:
    """
    Draws and manages the full touch control overlay.

    Layout (landscape):
      Left side : D-pad  (walk left/right + jump)
      Right side: Action buttons
        Row 1: SPACE (place), BACKSPACE (pick up), ENTER (evaluate)
        Row 2: digit picker strip  0-9
        Row 3: operator strip  + - * / ( )
        Row 4: special  S(Σ) I(∫) J(i) P S/Load B G T
    """

    def __init__(self, screen_w, screen_h):
        self.W = screen_w
        self.H = screen_h
        self._build_fonts()
        self._build_buttons()
        # Track active touches: {finger_id: (x, y)}
        self._fingers = {}
        # Digit picker state
        self._picker_open  = False
        self._picker_mode  = None   # "digit" | "op" | "special"

    def _build_fonts(self):
        for name in ["Consolas", "Courier New", None]:
            try:
                self.font_sm  = pygame.font.SysFont(name, 18, bold=True)
                self.font_xs  = pygame.font.SysFont(name, 13, bold=True)
                self.font_med = pygame.font.SysFont(name, 22, bold=True)
                return
            except Exception:
                pass
        self.font_sm  = pygame.font.Font(None, 18)
        self.font_xs  = pygame.font.Font(None, 13)
        self.font_med = pygame.font.Font(None, 22)

    def _build_buttons(self):
        W, H = self.W, self.H

        # D-pad on the left
        dp_cx = int(W * 0.10)
        dp_cy = int(H * 0.72)
        dp_r  = int(H * 0.10)   # radius of each arrow
        pad   = dp_r

        self.btn_left  = _VButton(dp_cx-pad-dp_r, dp_cy-dp_r, dp_r*2, dp_r*2,
                                  "◀", pygame.K_LEFT, "circle")
        self.btn_right = _VButton(dp_cx+pad,       dp_cy-dp_r, dp_r*2, dp_r*2,
                                  "▶", pygame.K_RIGHT, "circle")
        self.btn_up    = _VButton(dp_cx-dp_r, dp_cy-pad-dp_r, dp_r*2, dp_r*2,
                                  "▲", pygame.K_UP, "circle")

        # Main action buttons — right side
        bw, bh = int(W*0.12), int(H*0.09)
        gap     = int(W*0.015)
        rx      = int(W*0.60)
        ry      = int(H*0.60)

        self.btn_place    = _VButton(rx,             ry,      bw,    bh,    "PLACE\nSPACE", pygame.K_SPACE,     color=_ORANGE)
        self.btn_pickup   = _VButton(rx+bw+gap,      ry,      bw,    bh,    "PICK\n⌫",    pygame.K_BACKSPACE)
        self.btn_enter    = _VButton(rx+2*(bw+gap),  ry,      bw,    bh,    "EVAL\n↵",    pygame.K_RETURN,     color=(50,120,50,180))
        self.btn_clear    = _VButton(rx+3*(bw+gap),  ry,      bw,    bh,    "CLR\nC",     pygame.K_c)

        # Shield (SHIFT) and Flick (F) — for battle
        bw2 = int(W*0.10)
        self.btn_shield   = _VButton(rx,             ry+bh+gap, bw2, bh,   "🛡SHIFT", pygame.K_LSHIFT, color=(40,40,120,180))
        self.btn_flick    = _VButton(rx+bw2+gap,     ry+bh+gap, bw2, bh,   "FLICK\nF",   pygame.K_f,   color=(120,100,30,180))
        self.btn_shoot    = _VButton(rx+2*(bw2+gap), ry+bh+gap, bw2, bh,   "SHOOT\n▶",  pygame.K_SPACE, color=_ORANGE)
        self.btn_bag      = _VButton(rx+3*(bw2+gap), ry+bh+gap, bw2, bh,   "BAG\nB",    pygame.K_b)
        self.btn_gallery  = _VButton(rx+4*(bw2+gap), ry+bh+gap, bw2, bh,   "GALL\nG",   pygame.K_g)
        self.btn_trig     = _VButton(rx+5*(bw2+gap), ry+bh+gap, bw2, bh,   "TRIG\nT",   pygame.K_t)

        # Symbol picker toggle buttons
        pw  = int(W*0.09)
        px0 = int(W*0.60)
        py0 = int(H*0.88)
        labels_keys = [
            ("0-9", None, "digit"),
            ("+-*/", None, "op"),
            ("Σ∫i", None, "special"),
        ]
        self.btn_pickers = []
        for i,(lbl,_,mode) in enumerate(labels_keys):
            b = _VButton(px0 + i*(pw+gap), py0, pw, int(H*0.08),
                         lbl, None, color=(40,30,60,180))
            b._picker_mode = mode
            self.btn_pickers.append(b)

        # Digit picker strip (shown when picker open)
        self.picker_btns = []
        self._build_picker_strips(W, H)

        # Collect all persistent buttons
        self.persistent = [
            self.btn_left, self.btn_right, self.btn_up,
            self.btn_place, self.btn_pickup, self.btn_enter, self.btn_clear,
            self.btn_shield, self.btn_flick, self.btn_shoot,
            self.btn_bag, self.btn_gallery, self.btn_trig,
        ] + self.btn_pickers

        # Battle-only buttons (shown only during battle)
        self.battle_btns = [self.btn_shield, self.btn_flick, self.btn_shoot]
        # Calc-only (not in battle)
        self.calc_btns   = [self.btn_place, self.btn_pickup, self.btn_enter,
                             self.btn_clear, self.btn_bag, self.btn_gallery,
                             self.btn_trig] + self.btn_pickers

    def _build_picker_strips(self, W, H):
        """Build the expandable picker strips for digits, operators, specials."""
        self.picker_btns = {}

        sw   = int(W * 0.088)
        sh   = int(H * 0.085)
        gap  = int(W * 0.008)
        py   = int(H * 0.50)
        px0  = int(W * 0.40)

        # Digits
        digit_btns = []
        for i, d in enumerate("0123456789"):
            b = _VButton(px0 + i*(sw+gap), py, sw, sh, d, None)
            b._unicode = d
            digit_btns.append(b)
        self.picker_btns["digit"] = digit_btns

        # Operators
        op_btns = []
        ops = [("+","+"), ("-","-"), ("×","*"), ("÷","/"),
               ("(",  "("), (")",")"), ("^","**"), ("√","sqrt")]
        for i,(disp,key) in enumerate(ops):
            b = _VButton(px0 + i*(sw+gap), py, sw, sh, disp, None,
                         color=(54,34,72,180))
            b._unicode = key
            b._display = disp
            op_btns.append(b)
        self.picker_btns["op"] = op_btns

        # Specials
        spec_btns = []
        specs = [("Σ","s"),("∫","i_int"),("i(ι)","j"),
                 ("π","p"),("=","="),("%","%")]
        for i,(disp,key) in enumerate(specs):
            b = _VButton(px0 + i*(sw+gap), py, sw, sh, disp, None,
                         color=(20,55,80,180))
            b._unicode = key
            b._display = disp
            spec_btns.append(b)
        self.picker_btns["special"] = spec_btns

    def process_event(self, event, ts, in_battle=False):
        """
        Process a pygame event (FINGERDOWN/UP/MOTION or MOUSEBUTTONDOWN/UP).
        Updates TouchState ts accordingly.
        Returns True if the event was consumed by the overlay.
        """
        # Normalise: use mouse events on desktop, finger on Android
        if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION,
                          pygame.FINGERUP):
            # pygame normalises finger coords 0..1
            fx = int(event.x * self.W)
            fy = int(event.y * self.H)
            fid = event.finger_id

            if event.type == pygame.FINGERDOWN:
                self._fingers[fid] = (fx, fy)
                return self._handle_press(fx, fy, fid, ts, in_battle)
            elif event.type == pygame.FINGERUP:
                self._fingers.pop(fid, None)
                return self._handle_release(fid, ts)
            elif event.type == pygame.FINGERMOTION:
                self._fingers[fid] = (fx, fy)
                # treat motion as re-press
                self._handle_release(fid, ts)
                return self._handle_press(fx, fy, fid, ts, in_battle)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            fx, fy = event.pos
            return self._handle_press(fx, fy, 0, ts, in_battle)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self._handle_release(0, ts)

        return False

    def _all_active_btns(self, in_battle):
        buttons = [self.btn_left, self.btn_right, self.btn_up]
        if in_battle:
            buttons += self.battle_btns
        else:
            buttons += self.calc_btns
        if self._picker_open and self._picker_mode:
            buttons += self.picker_btns.get(self._picker_mode, [])
        return buttons

    def _handle_press(self, fx, fy, fid, ts, in_battle):
        # Check picker toggle buttons
        for pb in self.btn_pickers:
            if pb.contains(fx, fy):
                mode = pb._picker_mode
                if self._picker_open and self._picker_mode == mode:
                    self._picker_open = False
                    self._picker_mode = None
                else:
                    self._picker_open = True
                    self._picker_mode = mode
                pb.held = True
                pb._fid = fid
                return True

        # Check picker strip buttons
        if self._picker_open and self._picker_mode:
            for b in self.picker_btns.get(self._picker_mode, []):
                if b.contains(fx, fy):
                    b.held = True
                    b._fid = fid
                    u = getattr(b, "_unicode", None)
                    if u:
                        # Synthesise unicode press
                        ts._unicode_queue.append(u)
                        ts._just.add(pygame.K_RETURN)  # marker
                    self._picker_open = False
                    return True

        # Check regular buttons
        for b in self._all_active_btns(in_battle):
            if b.contains(fx, fy):
                b.held = True
                b._fid = fid
                if b.key:
                    ts.press(b.key)
                return True
        return False

    def _handle_release(self, fid, ts):
        for b in self.persistent:
            if getattr(b, "_fid", None) == fid:
                b.held = False
                b._fid = None
                if b.key:
                    ts.release(b.key)
        # Also release picker strip
        for strip in self.picker_btns.values():
            for b in strip:
                if getattr(b, "_fid", None) == fid:
                    b.held = False
                    b._fid = None
        return False

    def draw(self, surf, in_battle=False):
        """Draw the touch overlay."""
        # D-pad always
        for b in [self.btn_left, self.btn_right, self.btn_up]:
            b.draw(surf, self.font_sm, self.font_xs)

        # Context buttons
        if in_battle:
            for b in self.battle_btns:
                b.draw(surf, self.font_sm, self.font_xs)
        else:
            for b in self.calc_btns:
                b.draw(surf, self.font_sm, self.font_xs)

        # Picker toggle buttons
        for b in self.btn_pickers:
            b.draw(surf, self.font_sm, self.font_xs)

        # Open picker strip
        if self._picker_open and self._picker_mode:
            # Dim background for picker
            dim = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 80))
            surf.blit(dim, (0, 0))
            for b in self.picker_btns.get(self._picker_mode, []):
                b.draw(surf, self.font_sm, self.font_xs)
