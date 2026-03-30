"""
DIGIT KEEPER 2  —  Now with Sigma and Integration!
===================================================
The stick figure lives INSIDE the calculator display.
Pick up symbols and walk to place them. Special keys
S and I pick up the Sigma and Integral "guns" — when
placed, a popup appears to fill in the parameters.

Run:   python3 digit_keeper2.py

CONTROLS
  ← / A            Walk left
  → / D            Walk right
  ↑ / W            Jump
  0–9              Pick up digit
  + - * /          Pick up operator
  S                Pick up Sigma  (Σ)
  I                Pick up Integral (∫)
  SPACE            Place held symbol
  BACKSPACE        Delete nearest symbol
  ENTER            Evaluate expression  (or confirm popup)
  C                Clear all
  ESC              Quit  (or close popup)

POPUP (appears after placing Σ or ∫)
  TAB              Move to next field
  ENTER            Compute and place result
  ESC              Cancel
"""

import pygame
import math
import random
import sys

pygame.init()

W, H = 1200, 740
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Digit Keeper 2 — Sigma & Integral Edition")
clock = pygame.time.Clock()

# ── fonts ──────────────────────────────────────────────────
def make_font(size, bold=False):
    for name in ["Consolas", "Courier New", None]:
        try:    return pygame.font.SysFont(name, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

F_GIANT = make_font(72, bold=True)
F_BIG   = make_font(44, bold=True)
F_MED   = make_font(28, bold=True)
F_SM    = make_font(19, bold=True)
F_XS    = make_font(14)
F_TINY  = make_font(12)

# ── colors ─────────────────────────────────────────────────
BG          = (13,  13,  22)
CALC_BODY   = (24,  24,  38)
CALC_BORDER = (52,  52,  84)
DISP_BG     = (7,   18,  12)
DISP_BORDER = (36, 125,  62)
BTN_NUM     = (34,  34,  54)
BTN_OP      = (52,  32,  70)
BTN_EQ      = (22,  78,  50)
BTN_CLR     = (80,  24,  34)
BTN_SPEC    = (20,  55,  80)   # sigma/integral buttons
WHITE       = (232, 238, 255)
GREEN       = (62,  248, 122)
CYAN        = (0,   202, 248)
YELLOW      = (255, 222,  42)
ORANGE      = (255, 142,  28)
RED         = (255,  58,  58)
PURPLE      = (168,  68, 248)
GRAY        = (102, 102, 138)
DARK        = (14,   14,  26)
PINK        = (255, 102, 172)
LIME        = (128, 255,  78)
TEAL        = (0,   200, 180)
INDIGO      = (100,  80, 255)

# ── calculator geometry ────────────────────────────────────
CX, CY = 45, 18
CW, CH = 510, 690

DX = CX + 16
DY = CY + 32
DW = CW - 32
DH = 230

WORLD_LEFT  = DX + 10
WORLD_RIGHT = DX + DW - 10
WORLD_FLOOR = DY + DH - 10
WORLD_CEIL  = DY + 8

BAY   = DY + DH + 16
BTW   = 108
BTH   = 56
BTGAP = 6

BUTTON_DEFS = [
    ("C",    "C",    0, 0, BTN_CLR),
    ("sg",   "+/-",  1, 0, BTN_OP),
    ("%",    "%",    2, 0, BTN_OP),
    ("/",    "÷",    3, 0, BTN_OP),
    ("7",    "7",    0, 1, BTN_NUM),
    ("8",    "8",    1, 1, BTN_NUM),
    ("9",    "9",    2, 1, BTN_NUM),
    ("*",    "×",    3, 1, BTN_OP),
    ("4",    "4",    0, 2, BTN_NUM),
    ("5",    "5",    1, 2, BTN_NUM),
    ("6",    "6",    2, 2, BTN_NUM),
    ("-",    "-",    3, 2, BTN_OP),
    ("1",    "1",    0, 3, BTN_NUM),
    ("2",    "2",    1, 3, BTN_NUM),
    ("3",    "3",    2, 3, BTN_NUM),
    ("+",    "+",    3, 3, BTN_OP),
    ("0",    "0",    0, 4, BTN_NUM),
    (".",    ".",    1, 4, BTN_NUM),
    ("=",    "=",    2, 4, BTN_EQ),
    ("del",  "<",    3, 4, BTN_CLR),
    # Row 5 — special math
    ("SIG",  "S  Sigma",  0, 5, BTN_SPEC),
    ("INT",  "I  Integral",2, 5, BTN_SPEC),
]

def btn_rect(col, row):
    return pygame.Rect(
        CX + 16 + col * (BTW + BTGAP),
        BAY      + row * (BTH + BTGAP),
        BTW, BTH
    )

# Sigma and Integral buttons span 2 cols
BUTTONS = []
for k, t, c, r, bg in BUTTON_DEFS:
    rect = btn_rect(c, r)
    if k in ("SIG", "INT"):
        rect.width = BTW * 2 + BTGAP   # double width
    BUTTONS.append({"key": k, "text": t, "rect": rect, "bg": bg, "flash": 0})

def sym_color(key):
    if key == "+":   return GREEN
    if key == "-":   return CYAN
    if key == "*":   return ORANGE
    if key == "/":   return PURPLE
    if key == "=":   return LIME
    if key in ("C", "del"): return RED
    if key == "%":   return PINK
    if key in ("sg",): return YELLOW
    if key == ".":   return WHITE
    if key == "SIG": return TEAL
    if key == "INT": return INDIGO
    if key == "3.14159265358979": return (255, 215, 0)   # π is gold
    return YELLOW

# ── particles ──────────────────────────────────────────────
_px = []

def burst(x, y, col, n=10):
    for _ in range(n):
        _px.append({"x": float(x), "y": float(y),
                    "vx": random.uniform(-3, 3),
                    "vy": random.uniform(-4.5, -0.3),
                    "col": col,
                    "life": random.randint(28, 52),
                    "ml": 48, "r": random.randint(3, 6)})

def upd_px():
    for p in _px:
        p["x"] += p["vx"]; p["y"] += p["vy"]
        p["vy"] += 0.14;   p["life"] -= 1
    _px[:] = [p for p in _px if p["life"] > 0]

def draw_px(surf):
    for p in _px:
        a = p["life"] / p["ml"]
        c = tuple(min(255, int(ch*a)) for ch in p["col"])
        pygame.draw.circle(surf, c,
                           (int(p["x"]), int(p["y"])),
                           max(1, int(p["r"]*a)))

# ── placed symbols ─────────────────────────────────────────
placed      = []
result_text = ""
SLOT_SPACING = 42

def get_slot_x(i):
    return WORLD_LEFT + 22 + i * SLOT_SPACING

def find_insert_index(fig_x):
    for i, s in enumerate(placed):
        if fig_x < s["x"]:
            return i
    return len(placed)

def find_nearest_index(fig_x):
    if not placed: return None
    return min(range(len(placed)), key=lambda i: abs(placed[i]["x"] - fig_x))

def reflow():
    for i, s in enumerate(placed):
        s["x"] = float(get_slot_x(i))

# ── math engine ────────────────────────────────────────────
def safe_eval_expr(expr_str, var, val):
    """Evaluate expr_str with var substituted by val."""
    e = (expr_str.strip()
         .replace("^", "**")
         .replace(var, f"({val})")
         .replace("sin", "math.sin")
         .replace("cos", "math.cos")
         .replace("tan", "math.tan")
         .replace("sqrt", "math.sqrt")
         .replace("log", "math.log10")
         .replace("ln", "math.log")
         .replace("pi", "math.pi")
         .replace("e", "math.e"))
    return eval(e)

def compute_sigma(expr_str, n_from, n_to):
    total = 0.0
    for n in range(int(n_from), int(n_to) + 1):
        total += safe_eval_expr(expr_str, "n", n)
    return total

def compute_integral(expr_str, a, b, steps=1000):
    """Simpson's 1/3 rule."""
    if steps % 2 != 0:
        steps += 1
    h = (b - a) / steps
    total = safe_eval_expr(expr_str, "x", a) + safe_eval_expr(expr_str, "x", b)
    for i in range(1, steps):
        val = safe_eval_expr(expr_str, "x", a + i * h)
        total += val * (4 if i % 2 != 0 else 2)
    return (h / 3) * total

# ── popup state ────────────────────────────────────────────
# mode: None | "sigma" | "integral"
popup = {
    "mode":   None,
    "fields": [],       # list of {"label", "value", "hint"}
    "active": 0,        # which field is focused
    "error":  "",
    "result": "",
}

def open_popup(mode):
    popup["mode"]   = mode
    popup["error"]  = ""
    popup["result"] = ""
    popup["active"] = 0
    if mode == "sigma":
        popup["fields"] = [
            {"label": "From  n =", "value": "1",   "hint": "integer"},
            {"label": "To    n =", "value": "10",  "hint": "integer"},
            {"label": "f(n)     ", "value": "n**2","hint": "use n, e.g. n**2"},
        ]
    elif mode == "integral":
        popup["fields"] = [
            {"label": "From  a =", "value": "0",   "hint": "number"},
            {"label": "To    b =", "value": "1",   "hint": "number"},
            {"label": "f(x)     ", "value": "x**2","hint": "use x, e.g. x**2"},
        ]

def close_popup():
    popup["mode"] = None

def popup_type_char(ch):
    f = popup["fields"][popup["active"]]
    f["value"] += ch

def popup_backspace():
    f = popup["fields"][popup["active"]]
    f["value"] = f["value"][:-1]

def popup_next_field():
    popup["active"] = (popup["active"] + 1) % len(popup["fields"])

def popup_compute():
    """Try to compute. Returns (value_str, label_str) or raises."""
    fields = popup["fields"]
    f0 = fields[0]["value"].strip()
    f1 = fields[1]["value"].strip()
    f2 = fields[2]["value"].strip()

    if popup["mode"] == "sigma":
        n_from = int(float(f0))
        n_to   = int(float(f1))
        if n_to - n_from > 100000:
            raise ValueError("Range too large")
        result = compute_sigma(f2, n_from, n_to)
        label  = f"S({f2},{f0},{f1})"
    else:
        a = float(f0)
        b = float(f1)
        result = compute_integral(f2, a, b)
        label  = f"I({f2},{f0},{f1})"

    val = f"{result:.6f}".rstrip("0").rstrip(".")
    return val, label

def draw_popup(surf):
    if popup["mode"] is None:
        return

    is_sigma = popup["mode"] == "sigma"
    sym      = "Σ" if is_sigma else "∫"
    col      = TEAL if is_sigma else INDIGO
    title    = "SIGMA  SUMMATION" if is_sigma else "DEFINITE  INTEGRAL"

    # Overlay dim
    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    surf.blit(dim, (0, 0))

    # Panel
    pw, ph = 520, 320
    px = W // 2 - pw // 2
    py = H // 2 - ph // 2

    pygame.draw.rect(surf, (18, 18, 32), (px, py, pw, ph), border_radius=14)
    pygame.draw.rect(surf, col,          (px, py, pw, ph), 3,  border_radius=14)

    # Title
    ts = F_MED.render(sym + "  " + title, True, col)
    surf.blit(ts, (px + pw//2 - ts.get_width()//2, py + 14))

    # Fields
    fy = py + 60
    for i, field in enumerate(popup["fields"]):
        active = (i == popup["active"])
        lbl = F_XS.render(field["label"], True, col if active else GRAY)
        surf.blit(lbl, (px + 20, fy))

        # Input box
        box = pygame.Rect(px + 160, fy - 4, 280, 28)
        pygame.draw.rect(surf, DARK, box, border_radius=5)
        pygame.draw.rect(surf, col if active else GRAY, box, 2, border_radius=5)

        val_text = field["value"]
        if active and (pygame.time.get_ticks() // 500) % 2 == 0:
            val_text += "|"
        vs = F_SM.render(val_text, True, WHITE if active else GRAY)
        surf.blit(vs, (box.x + 6, box.y + 4))

        # Hint
        hs = F_TINY.render(field["hint"], True, (60, 60, 90))
        surf.blit(hs, (box.right + 6, fy + 4))

        fy += 46

    # Error
    if popup["error"]:
        es = F_XS.render("ERROR: " + popup["error"], True, RED)
        surf.blit(es, (px + pw//2 - es.get_width()//2, fy + 4))

    # Result preview
    if popup["result"]:
        rs = F_MED.render("= " + popup["result"], True, GREEN)
        surf.blit(rs, (px + pw//2 - rs.get_width()//2, fy + 4))

    # Instructions
    inst = [
        "TAB — next field",
        "ENTER — compute & place",
        "ESC — cancel",
    ]
    ix = px + 20
    iy = py + ph - 36
    for ins in inst:
        s = F_TINY.render(ins, True, GRAY)
        surf.blit(s, (ix, iy))
        ix += s.get_width() + 24

    # Big symbol decoration
    big = F_GIANT.render(sym, True, (*col, 40) if False else col)
    alpha_surf = pygame.Surface((big.get_width(), big.get_height()), pygame.SRCALPHA)
    alpha_surf.fill((0,0,0,0))
    big_dim = make_font(72, bold=True).render(sym, True, (*col[:3], 30))
    surf.blit(big_dim, (px + pw - big_dim.get_width() - 10, py + 10))

# ── figure ─────────────────────────────────────────────────
class Figure:
    SPEED  = 3.8
    GRAV   = 0.55
    JUMP_V = -11.0

    def __init__(self):
        self.x  = float(DX + DW // 2)
        self.y  = float(WORLD_FLOOR)
        self.vx = 0.0
        self.vy = 0.0
        self.grounded    = True
        self.j_held      = False
        self.walk_t      = 0.0
        self.facing      = 1
        self.held_key    = None
        self.held_text   = None
        self.held_col    = WHITE
        self.held_scale  = 1.0
        self.anim_place     = 0
        self.anim_pickup    = 0
        self.anim_celebrate = 0
        self.anim_blink     = 0
        self.anim_squat     = 0   # squatting down to pick up

    def pick(self, key, text):
        self.held_key   = key
        self.held_text  = text
        self.held_col   = sym_color(key)
        self.held_scale = 1.6
        self.anim_pickup = 18
        burst(int(self.x), int(self.y)-40, self.held_col, n=14)

    def drop(self):
        if self.held_key:
            burst(int(self.x), int(self.y)-30, RED, n=8)
        self.held_key  = None
        self.held_text = None

    def place(self):
        global result_text
        if self.held_key is None:
            return

        key  = self.held_key
        text = self.held_text

        # Special: Sigma/Integral open a popup instead of placing raw text
        if key in ("SIG", "INT"):
            open_popup("sigma" if key == "SIG" else "integral")
            self.held_key  = None
            self.held_text = None
            self.anim_place = 18
            return

        result_text = ""
        idx = find_insert_index(self.x)
        placed.insert(idx, {
            "x":        float(get_slot_x(idx)),
            "text":     text,
            "key":      key,
            "scale":    1.4,
            "vy":       -6.0,
            "grounded": False,
            "y":        float(WORLD_FLOOR - 24),
        })
        reflow()
        burst(int(self.x), int(self.y)-30, self.held_col, n=16)
        self.anim_place     = 18
        self.anim_celebrate = 38
        self.held_key  = None
        self.held_text = None

    def place_value(self, val_str, label_str, col):
        """Called after popup compute — places result as a token."""
        global result_text
        result_text = ""
        idx = find_insert_index(self.x)
        placed.insert(idx, {
            "x":        float(get_slot_x(idx)),
            "text":     val_str,
            "key":      val_str,
            "label":    label_str,
            "scale":    1.5,
            "vy":       -7.0,
            "grounded": False,
            "y":        float(WORLD_FLOOR - 24),
            "special_col": col,
        })
        reflow()
        burst(int(self.x), int(self.y)-30, col, n=22)
        self.anim_place     = 20
        self.anim_celebrate = 50

    def delete_nearest(self):
        """Pick up the nearest placed symbol — figure walks over and lifts it."""
        global result_text
        idx = find_nearest_index(self.x)
        if idx is None:
            return

        sym = placed[idx]

        # If already holding something, drop it first
        if self.held_key:
            self.drop()

        # Pick up the symbol from the display
        key  = sym["key"]
        text = sym["text"]
        col  = sym.get("special_col", sym_color(key))

        self.held_key   = key
        self.held_text  = text
        self.held_col   = col
        self.held_scale = 1.5
        self.anim_pickup    = 22
        self.anim_celebrate = 30
        self.anim_squat     = 18   # squat down first

        # Remove from placed list
        placed.pop(idx)
        reflow()
        result_text = ""

        # Pickup burst — rises from floor up to figure's hands
        burst(int(sym["x"]), WORLD_FLOOR - 20, col, n=14)

    def handle_keys(self, keys):
        if popup["mode"]:
            return   # don't move while popup open
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.SPEED; self.facing = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.SPEED;  self.facing =  1
        else:
            self.vx *= 0.5

        want_jump = keys[pygame.K_UP] or keys[pygame.K_w]
        if want_jump and not self.j_held and self.grounded:
            self.vy = self.JUMP_V
            self.grounded = False
            burst(int(self.x), int(self.y), CYAN, n=6)
        self.j_held = bool(want_jump)

        if abs(self.vx) > 0.3:
            self.walk_t += 0.22

    def update(self):
        if popup["mode"]:
            self.vx = 0
            return

        self.x += self.vx
        self.x  = max(float(WORLD_LEFT), min(float(WORLD_RIGHT), self.x))

        self.vy += self.GRAV
        self.y  += self.vy

        self.grounded = False
        if self.vy >= 0 and self.y >= WORLD_FLOOR:
            self.y = float(WORLD_FLOOR)
            self.vy = 0.0
            self.grounded = True

        if self.y < WORLD_CEIL + 44:
            self.y  = float(WORLD_CEIL + 44)
            self.vy = max(0.0, self.vy)

        if self.held_scale > 1.0:
            self.held_scale = max(1.0, self.held_scale - 0.06)
        if self.anim_place     > 0: self.anim_place     -= 1
        if self.anim_pickup    > 0: self.anim_pickup     -= 1
        if self.anim_celebrate > 0: self.anim_celebrate  -= 1
        if self.anim_blink     > 0: self.anim_blink      -= 1
        if self.anim_squat     > 0: self.anim_squat       -= 1
        if random.random() < 0.004: self.anim_blink = 9

    def draw(self, surf):
        x  = int(self.x)
        fy = int(self.y)
        # Squat offset — body crouches down when picking up
        squat = int(10 * (self.anim_squat / 18)) if self.anim_squat > 0 else 0
        fy   -= squat          # feet stay, body rises less (squat effect)
        hy    = fy - 36 + squat*2   # head comes down
        cel  = self.anim_celebrate > 0
        pick = self.anim_pickup    > 0

        pygame.draw.ellipse(surf, (20, 45, 25), (x-12, fy+1, 24, 6))
        pygame.draw.circle(surf, WHITE, (x, hy), 11, 2)

        # eyes
        if self.anim_blink > 0:
            pygame.draw.line(surf, WHITE, (x-4, hy-2), (x-1, hy-2), 2)
            pygame.draw.line(surf, WHITE, (x+1, hy-2), (x+4, hy-2), 2)
        else:
            pygame.draw.circle(surf, WHITE, (x-4, hy-2), 2)
            pygame.draw.circle(surf, WHITE, (x+4, hy-2), 2)

        # mouth
        if cel:
            pygame.draw.arc(surf, YELLOW,
                            pygame.Rect(x-5, hy+4, 10, 7), math.pi, 2*math.pi, 2)
        else:
            pygame.draw.line(surf, WHITE, (x-4, hy+5), (x+4, hy+5), 2)

        pygame.draw.line(surf, WHITE, (x, hy+11), (x, fy-10), 2)

        sw = int(10*math.sin(self.walk_t)) if abs(self.vx) > 0.2 else 0
        pygame.draw.line(surf, WHITE, (x, fy-10), (x-sw, fy), 2)
        pygame.draw.line(surf, WHITE, (x, fy-10), (x+sw, fy), 2)

        if self.held_key:
            lift = -14 if not cel else -18 + int(4*math.sin(self.walk_t*3))
            pygame.draw.line(surf, WHITE, (x, hy+13), (x-17, hy+lift), 2)
            pygame.draw.line(surf, WHITE, (x, hy+13), (x+17, hy+lift), 2)

            hcol = self.held_col
            gs = pygame.Surface((70, 70), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*hcol, 50), (35, 35), 32)
            surf.blit(gs, (x-35, hy-68))

            sc = self.held_scale
            s  = F_BIG.render(self.held_text, True, hcol)
            if sc != 1.0:
                nw, nh = int(s.get_width()*sc), int(s.get_height()*sc)
                s = pygame.transform.scale(s, (nw, nh))
            surf.blit(s, (x - s.get_width()//2, hy - 72 - s.get_height()//2))

            if cel or pick:
                for i in range(5):
                    ang = self.walk_t*4 + i*2*math.pi/5
                    pygame.draw.circle(surf, hcol,
                                       (x + int(28*math.cos(ang)),
                                        hy - 68 + int(10*math.sin(ang))), 3)

            hint = F_TINY.render("SPACE = place", True, hcol)
            surf.blit(hint, (x - hint.get_width()//2, hy - 100))

            # caret
            if (pygame.time.get_ticks() // 300) % 2 == 0:
                cx2 = get_slot_x(find_insert_index(self.x))
                pygame.draw.line(surf, hcol,
                                 (int(cx2), WORLD_FLOOR-28), (int(cx2), WORLD_FLOOR-4), 2)
                pygame.draw.polygon(surf, hcol, [
                    (int(cx2)-5, WORLD_FLOOR-6),
                    (int(cx2)+5, WORLD_FLOOR-6),
                    (int(cx2),   WORLD_FLOOR),
                ])
        elif self.anim_place > 0:
            t2 = self.walk_t * 4
            pygame.draw.line(surf, WHITE, (x, hy+13),
                             (x-17, hy + int(5*math.sin(t2))), 2)
            pygame.draw.line(surf, WHITE, (x, hy+13),
                             (x+17, hy + int(5*math.sin(t2+1))), 2)
        else:
            sw2 = int(8*math.sin(self.walk_t+math.pi)) if abs(self.vx)>0.2 else 0
            pygame.draw.line(surf, WHITE, (x, hy+13), (x-14, fy-20+sw2), 2)
            pygame.draw.line(surf, WHITE, (x, hy+13), (x+14, fy-20-sw2), 2)

# ── update placed symbol animations ───────────────────────
def update_placed():
    for sym in placed:
        if not sym.get("grounded", True):
            sym["y"]  = sym.get("y", float(WORLD_FLOOR-24)) + sym.get("vy", 0)
            sym["vy"] = sym.get("vy", 0) + 0.5
            if sym.get("y", WORLD_FLOOR) >= WORLD_FLOOR - 24:
                sym["y"]  = float(WORLD_FLOOR - 24)
                sym["vy"] = 0.0
                sym["grounded"] = True
        if sym.get("scale", 1.0) > 1.0:
            sym["scale"] = max(1.0, sym["scale"] - 0.06)

def draw_placed(surf):
    for sym in placed:
        sx  = int(sym["x"])
        sy  = int(sym.get("y", float(WORLD_FLOOR - 24)))
        sc  = sym.get("scale", 1.0)
        col = sym.get("special_col", sym_color(sym["key"]))

        # For special (sigma/integral result), draw with bracket decoration
        is_special = "label" in sym

        s = F_MED.render(sym["text"], True, col)
        if sc != 1.0:
            nw, nh = int(s.get_width()*sc), int(s.get_height()*sc)
            s = pygame.transform.scale(s, (nw, nh))
        surf.blit(s, (sx - s.get_width()//2, sy - s.get_height()//2))

        if is_special:
            # small label above showing what this value came from
            lbl = sym.get("label", "")
            ls  = F_TINY.render(lbl, True, tuple(c//2 for c in col))
            surf.blit(ls, (sx - ls.get_width()//2, sy - s.get_height()//2 - 14))
            # coloured underline
            pygame.draw.line(surf, col,
                             (sx-14, WORLD_FLOOR-4), (sx+14, WORLD_FLOOR-4), 2)
        else:
            pygame.draw.line(surf, tuple(c//2 for c in col),
                             (sx-12, WORLD_FLOOR-4), (sx+12, WORLD_FLOOR-4), 1)

# ═══════════════════════════════════════════════════════════
#  PI BATTLE SYSTEM
# ═══════════════════════════════════════════════════════════

PI_APPROX_EXPRS = [
    "22/7", "314/100", "3.14", "3.142", "3.1416",
    "355/113", "3141/1000", "31416/10000",
    "3.14159", "3.141592", "3.1415926",
]
PI_VALUE = math.pi

pi_battle_done    = False   # one-time flag
pi_unlocked       = False   # player can use π after winning
pi_battle_active  = False   # are we in the battle right now?

# ── Pi battle constants ────────────────────────────────────
PB_W, PB_H = W, H   # battle takes full screen

PB_ORANGE = (255, 160,  40)
PB_GOLD   = (255, 215,   0)
PB_RED    = (220,  40,  40)
PB_CYAN   = (  0, 200, 240)
PB_GREEN  = ( 50, 240, 110)
PB_WHITE  = (230, 235, 255)
PB_PURPLE = (160,  60, 240)
PB_GRAY   = (110, 110, 145)
PB_DARK   = ( 12,  10,  22)
PB_PINK   = (255,  90, 170)

def _pb_font(size, bold=False):
    for n in ["Consolas","Courier New",None]:
        try: return pygame.font.SysFont(n, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

PBF_LG = _pb_font(56, bold=True)
PBF_MD = _pb_font(34, bold=True)
PBF_SM = _pb_font(22)
PBF_XS = _pb_font(15)

# ── Pi battle particles ────────────────────────────────────
pb_particles = []

def pb_burst(x, y, col, n=12, texts=None):
    for _ in range(n):
        t = random.choice(texts) if texts else None
        pb_particles.append({
            "x": float(x), "y": float(y),
            "vx": random.uniform(-3.5, 3.5),
            "vy": random.uniform(-5, -0.5),
            "col": col, "text": t,
            "life": random.randint(30, 65), "ml": 55,
            "r": random.randint(3, 7)
        })

def pb_upd_particles():
    for p in pb_particles:
        p["x"]+=p["vx"]; p["y"]+=p["vy"]
        p["vy"]+=0.13;   p["life"]-=1
    pb_particles[:] = [p for p in pb_particles if p["life"]>0]

def pb_draw_particles(surf):
    for p in pb_particles:
        a = p["life"]/p["ml"]
        c = tuple(min(255,int(ch*a)) for ch in p["col"])
        if p["text"]:
            s = PBF_XS.render(p["text"],True,c)
            surf.blit(s,(int(p["x"]),int(p["y"])))
        else:
            r = max(1,int(p["r"]*a))
            pygame.draw.circle(surf,c,(int(p["x"]),int(p["y"])),r)

# ── Pi projectile classes ──────────────────────────────────
class PbShot:
    """Base battle projectile."""
    def __init__(self, x, y, dx, dy, owner, damage=10):
        self.x, self.y   = float(x), float(y)
        self.dx, self.dy = dx, dy
        self.owner  = owner
        self.damage = damage
        self.alive  = True
        self.trail  = []
        self.age    = 0

    def update(self):
        self.trail.append((int(self.x),int(self.y)))
        if len(self.trail)>14: self.trail.pop(0)
        self.x += self.dx; self.y += self.dy
        self.age += 1
        if not (-60<self.x<PB_W+60 and -60<self.y<PB_H+60):
            self.alive = False

    def rect(self):
        return pygame.Rect(self.x-7,self.y-7,14,14)

class DigitShot(PbShot):
    """Player fires digit/operator projectiles."""
    SYMS = ["+","−","×","÷","²","√","∞"]
    def __init__(self,x,y,dx,dy):
        super().__init__(x,y,dx,dy,"player",damage=12)
        self.sym = random.choice(self.SYMS)
        self.angle = 0
    def update(self):
        super().update(); self.angle+=10
    def draw(self,surf):
        for i,(tx,ty) in enumerate(self.trail):
            a=i/max(len(self.trail),1)
            c=tuple(int(ch*a*0.7) for ch in PB_GOLD)
            pygame.draw.circle(surf,c,(tx,ty),max(1,int(6*a)))
        s=PBF_SM.render(self.sym,True,PB_GOLD)
        rot=pygame.transform.rotate(s,self.angle)
        r=rot.get_rect(center=(int(self.x),int(self.y)))
        surf.blit(rot,r)

class SigmaBeam(PbShot):
    """Player's Σ weapon — slow, high damage."""
    def __init__(self,x,y,dx,dy):
        super().__init__(x,y,dx*0.65,dy*0.65,"player",damage=28)
        self.angle=0
    def update(self):
        super().update(); self.angle+=9
    def draw(self,surf):
        for i,(tx,ty) in enumerate(self.trail):
            a=i/max(len(self.trail),1)
            c=tuple(int(ch*a*0.6) for ch in PB_CYAN)
            pygame.draw.circle(surf,c,(tx,ty),max(1,int(10*a)))
        s=PBF_MD.render("Σ",True,PB_CYAN)
        rot=pygame.transform.rotate(s,self.angle)
        surf.blit(rot,rot.get_rect(center=(int(self.x),int(self.y))))
        pygame.draw.circle(surf,PB_CYAN,(int(self.x),int(self.y)),18,2)

class IntBeam(PbShot):
    """Player's ∫ weapon — very slow, very high damage."""
    def __init__(self,x,y,dx,dy):
        super().__init__(x,y,dx*0.45,dy*0.45,"player",damage=42)
    def draw(self,surf):
        for i,(tx,ty) in enumerate(self.trail):
            a=i/max(len(self.trail),1)
            c=tuple(int(ch*a*0.7) for ch in PB_PURPLE)
            pygame.draw.circle(surf,c,(tx,ty),max(1,int(7*a)))
        s=PBF_MD.render("∫",True,PB_PURPLE)
        surf.blit(s,(int(self.x)-10,int(self.y)-16))
        pygame.draw.circle(surf,PB_PURPLE,(int(self.x),int(self.y)),
                           22+int(4*math.sin(self.age*0.3)),2)

class PiBeam(PbShot):
    """Pi boss fires digits of pi as projectiles."""
    PI_DIGITS = ["3",".","1","4","1","5","9","2","6","5","3","5"]
    def __init__(self,x,y,dx,dy):
        super().__init__(x,y,dx,dy,"enemy",damage=14)
        self.digit = random.choice(self.PI_DIGITS)
        self.angle = 0
    def update(self):
        super().update(); self.angle+=6; self.dy+=0.04
    def draw(self,surf):
        for i,(tx,ty) in enumerate(self.trail):
            a=i/max(len(self.trail),1)
            c=tuple(int(ch*a) for ch in PB_ORANGE)
            pygame.draw.circle(surf,c,(tx,ty),max(1,int(6*a)))
        s=PBF_SM.render(self.digit,True,PB_ORANGE)
        rot=pygame.transform.rotate(s,self.angle)
        surf.blit(rot,rot.get_rect(center=(int(self.x),int(self.y))))
        pygame.draw.circle(surf,PB_ORANGE,(int(self.x),int(self.y)),14,2)

# ── Pi Boss ────────────────────────────────────────────────
class PiBoss:
    PHASES = ["CURIOUS","ENRAGED","IRRATIONAL"]

    def __init__(self):
        self.x   = float(PB_W - 180)
        self.y   = float(PB_H // 2)
        self.hp  = 250
        self.maxhp = 250
        self.phase = 0
        self.age   = 0
        self.shoot_timer = 0
        self.target_y    = float(PB_H//2)
        self.move_timer  = 0
        self.pattern     = 0
        self.hit_flash   = 0
        self.angry_t     = 0

    @property
    def shoot_rate(self):
        return max(16, 50 - self.phase*10)

    def update(self, py):
        self.age += 1
        if self.hit_flash>0: self.hit_flash-=1
        if self.angry_t >0: self.angry_t -=1

        ratio = self.hp/self.maxhp
        if   ratio > 0.60: self.phase = 0
        elif ratio > 0.25: self.phase = 1
        else:              self.phase = 2

        # Hover / track
        self.move_timer+=1
        if self.move_timer>45:
            self.target_y = py + random.randint(-90,90)
            self.target_y = max(80, min(PB_H-80, self.target_y))
            self.move_timer=0
        self.y += (self.target_y-self.y)*0.045

        # Phase 2: drift horizontally
        if self.phase==2:
            self.x = PB_W-180 + 35*math.sin(self.age*0.05)

    def shoot(self, px, py):
        shots=[]
        dx=px-self.x; dy=py-self.y
        dist=math.hypot(dx,dy) or 1
        ndx,ndy=dx/dist,dy/dist
        spd=4.5+self.phase*0.9

        pat=self.pattern%(3+self.phase)
        if pat==0:
            shots.append(PiBeam(self.x-20,self.y,ndx*spd,ndy*spd))
        elif pat==1:
            for off in [-20,0,20]:
                rad=math.radians(off)
                rdx=ndx*math.cos(rad)-ndy*math.sin(rad)
                rdy=ndx*math.sin(rad)+ndy*math.cos(rad)
                shots.append(PiBeam(self.x-20,self.y,rdx*spd,rdy*spd))
        elif pat==2:
            for i in range(6):
                ang=math.radians(i*60+self.age*4)
                shots.append(PiBeam(self.x-20,self.y,
                    math.cos(ang)*spd,math.sin(ang)*spd))
        else:
            shots.append(PiBeam(self.x-20,self.y,ndx*spd,ndy*spd))
            for _ in range(2):
                a=random.uniform(0,2*math.pi)
                shots.append(PiBeam(self.x-20,self.y,
                    math.cos(a)*spd*0.7,math.sin(a)*spd*0.7))
        self.pattern+=1
        return shots

    def take_damage(self,dmg):
        self.hp=max(0,self.hp-dmg)
        self.hit_flash=12
        self.angry_t=55
        pb_burst(int(self.x),int(self.y),PB_ORANGE,n=18,
                 texts=["π resists!","3.14...","irrational!"])

    def draw(self,surf):
        x,y=int(self.x),int(self.y)
        phase_cols=[PB_GOLD,PB_ORANGE,PB_RED]
        col=phase_cols[self.phase]
        hit=self.hit_flash>0

        # Aura
        aura_r=55+int(8*math.sin(self.age*0.07))
        for r in range(aura_r,aura_r-22,-5):
            gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            a=max(0,int(28*(1-(aura_r-r)/22)))
            pygame.draw.circle(gs,(*col,a),(r,r),r)
            surf.blit(gs,(x-r,y-r))

        # Main π symbol
        c=PB_WHITE if hit else col
        big=PBF_LG.render("π",True,c)
        surf.blit(big,(x-big.get_width()//2,y-big.get_height()//2))

        # Orbiting pi digits
        digits="3.14159265"
        for i,d in enumerate(digits):
            ang=self.age*0.04+i*(2*math.pi/len(digits))
            r=68+8*math.sin(self.age*0.06+i)
            sx2=x+int(r*math.cos(ang))
            sy2=y+int(r*math.sin(ang))
            ds=PBF_XS.render(d,True,col)
            surf.blit(ds,(sx2-ds.get_width()//2,sy2-ds.get_height()//2))

        # Angry quote
        if self.angry_t>0:
            quotes=["I AM IRRATIONAL!","YOU CAN'T CONTAIN ME!",
                    "3.14159265358979...","INFINITY IS MY HOME!",
                    "NO FRACTION CAN HOLD ME!"]
            q=quotes[(self.pattern//3)%len(quotes)]
            qs=PBF_SM.render(q,True,PB_RED)
            surf.blit(qs,(x-qs.get_width()//2,y-85))

    def rect(self):
        return pygame.Rect(self.x-38,self.y-38,76,76)

# ── Battle player (separate from calc figure) ─────────────
class BattlePlayer:
    SPEED=4.5
    WEAPONS=[DigitShot,SigmaBeam,IntBeam]
    W_NAMES=["+Digit","Σ Sigma","∫ Integral"]
    W_COLS=[PB_GOLD,PB_CYAN,PB_PURPLE]
    COOLDOWNS=[10,26,44]

    def __init__(self):
        self.x=float(180)
        self.y=float(PB_H//2)
        self.hp=150; self.maxhp=150
        self.weapon=0; self.cooldown=0
        self.inv=0; self.score=0
        self.facing=1; self.walk_t=0
        self.shooting=0

    def handle_input(self,keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  self.x-=self.SPEED; self.facing=-1
        if keys[pygame.K_RIGHT]or keys[pygame.K_d]:  self.x+=self.SPEED; self.facing= 1
        if keys[pygame.K_UP]   or keys[pygame.K_w]:  self.y-=self.SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  self.y+=self.SPEED
        self.x=max(20,min(PB_W//2-40,self.x))
        self.y=max(40,min(PB_H-40,   self.y))
        self.walk_t+=0.18
        if keys[pygame.K_1]: self.weapon=0
        if keys[pygame.K_2]: self.weapon=1
        if keys[pygame.K_3]: self.weapon=2

    def shoot(self):
        if self.cooldown>0: return None
        self.cooldown=self.COOLDOWNS[self.weapon]
        self.shooting=10
        cls=self.WEAPONS[self.weapon]
        p=cls(self.x+20*self.facing,self.y-5,9*self.facing,0)
        pb_burst(int(self.x+20*self.facing),int(self.y-5),
                 self.W_COLS[self.weapon],n=6)
        return p

    def update(self):
        if self.cooldown>0: self.cooldown-=1
        if self.inv>0:      self.inv-=1
        if self.shooting>0: self.shooting-=1

    def take_damage(self,dmg):
        if self.inv>0: return
        self.hp=max(0,self.hp-dmg)
        self.inv=45
        pb_burst(int(self.x),int(self.y),PB_RED,n=14,texts=["-"+str(dmg)])

    def draw(self,surf):
        x,y=int(self.x),int(self.y)
        if self.inv>0 and (self.inv//5)%2==0: return
        col=PB_WHITE
        pygame.draw.circle(surf,col,(x,y-28),12,2)
        pygame.draw.line(surf,col,(x,y-16),(x,y+10),2)
        lsway=int(10*math.sin(self.walk_t))
        pygame.draw.line(surf,col,(x,y+10),(x-lsway,y+32),2)
        pygame.draw.line(surf,col,(x,y+10),(x+lsway,y+32),2)
        if self.shooting>0:
            pygame.draw.line(surf,col,(x,y-6),(x+22*self.facing,y-6),2)
            pygame.draw.line(surf,col,(x,y-6),(x-8*self.facing,y+6),2)
        else:
            asway=int(8*math.sin(self.walk_t+math.pi))
            pygame.draw.line(surf,col,(x,y-6),(x-14,y+4+asway),2)
            pygame.draw.line(surf,col,(x,y-6),(x+14,y+4-asway),2)
        # weapon label
        ws=PBF_XS.render(self.W_NAMES[self.weapon],True,self.W_COLS[self.weapon])
        surf.blit(ws,(x-ws.get_width()//2,y-52))

    def rect(self):
        return pygame.Rect(self.x-14,self.y-40,28,72)

# ── Battle background drifters ─────────────────────────────
class PiBgSym:
    SYMS=["π","3.14","22/7","π²","2π","π/2","sin(π)","cos(π)","e^iπ",
          "3.14159","355/113","π≈3","τ/2","πr²"]
    def __init__(self):
        self.reset()
    def reset(self):
        self.x=random.randint(0,PB_W)
        self.y=random.randint(-40,PB_H+40)
        self.vy=random.uniform(0.2,0.8)
        self.sym=random.choice(self.SYMS)
    def update(self):
        self.y+=self.vy
        if self.y>PB_H+40: self.reset(); self.y=-10
    def draw(self,surf):
        s=pygame.font.Font(None,16).render(self.sym,True,(55,45,80))
        surf.blit(s,(int(self.x),int(self.y)))

pi_bg_syms=[PiBgSym() for _ in range(55)]

# ── Battle HUD ─────────────────────────────────────────────
def draw_pb_hud(surf, bp, boss):
    def hbar(x,y,w,h,hp,mx,col,lbl):
        pygame.draw.rect(surf,(25,25,42),(x,y,w,h),border_radius=4)
        f=int(w*hp/mx)
        if f>0: pygame.draw.rect(surf,col,(x,y,f,h),border_radius=4)
        pygame.draw.rect(surf,PB_GRAY,(x,y,w,h),2,border_radius=4)
        ls=PBF_XS.render(f"{lbl} {hp}/{mx}",True,PB_WHITE)
        surf.blit(ls,(x,y-18))

    hbar(20,30,200,16,bp.hp,bp.maxhp,PB_GREEN,"HP")
    for i,(wn,wc) in enumerate(zip(bp.W_NAMES,bp.W_COLS)):
        bx=20+i*90; by=60
        border=2 if bp.weapon==i else 1
        col=wc if bp.weapon==i else PB_GRAY
        pygame.draw.rect(surf,(20,20,35),(bx,by,82,22),border_radius=4)
        pygame.draw.rect(surf,col,(bx,by,82,22),border,border_radius=4)
        ws=PBF_XS.render(f"[{i+1}]{wn}",True,col)
        surf.blit(ws,(bx+3,by+4))

    phase_cols=[PB_GOLD,PB_ORANGE,PB_RED]
    hbar(PB_W-320,30,300,16,max(0,boss.hp),boss.maxhp,
         phase_cols[boss.phase],"π")
    pn=PBF_XS.render(f"PHASE: {boss.PHASES[boss.phase]}",True,
                     phase_cols[boss.phase])
    surf.blit(pn,(PB_W-320,52))

    hint=PBF_XS.render("WASD:Move | SPACE:Shoot | 1-2-3:Weapon",True,PB_GRAY)
    surf.blit(hint,(PB_W//2-hint.get_width()//2,8))

# ── Battle screen flash ────────────────────────────────────
pb_flash=0; pb_flash_col=PB_WHITE
def pb_trigger_flash(col=PB_WHITE,s=80):
    global pb_flash,pb_flash_col
    pb_flash=s; pb_flash_col=col

# ── Battle state machine ───────────────────────────────────
# States: None | "intro" | "fight" | "win" | "lose"
pb_state     = None
pb_intro_t   = 0
pb_player    = None
pb_boss      = None
pb_shots     = []
pb_post_t    = 0   # countdown after win/lose before returning

def start_pi_battle():
    global pb_state,pb_intro_t,pb_player,pb_boss,pb_shots
    global pb_particles,pb_flash
    pb_state   = "intro"
    pb_intro_t = 0
    pb_player  = BattlePlayer()
    pb_boss    = PiBoss()
    pb_shots   = []
    pb_particles.clear()
    pb_flash   = 0

def draw_pb_intro(surf, t):
    # Dark gradient bg
    for row in range(0,PB_H,4):
        frac=row/PB_H
        r=int(8+12*frac); g=int(6+4*frac); b=int(18+14*frac)
        pygame.draw.line(surf,(r,g,b),(0,row),(PB_W,row))

    lines=[
        (0,   "You entered an approximation of π..."),
        (80,  "3.14...  22/7...  355/113..."),
        (160, "But π is IRRATIONAL."),
        (240, "It cannot be contained in a fraction."),
        (320, "π has AWAKENED — and it is ANGRY."),
        (400, "DEFEAT π to unlock it as a symbol!"),
        (480, "Press SPACE to fight!"),
    ]
    y0=150
    for start,text in lines:
        if t>=start:
            col=PB_RED if "ANGRY" in text or "AWAKENED" in text else \
                PB_GOLD if "DEFEAT" in text else PB_WHITE
            fs=PBF_SM.render(text,True,col)
            surf.blit(fs,(PB_W//2-fs.get_width()//2,y0))
        y0+=46

    # Animated π forming
    if t>=320:
        bx,by=PB_W-220,PB_H//2
        col=PB_RED if t>=400 else PB_ORANGE
        ps=PBF_LG.render("π",True,col)
        surf.blit(ps,(bx-ps.get_width()//2,by-ps.get_height()//2))
        for i,d in enumerate("3.14159"):
            ang=t*0.05+i*math.pi*2/7
            dx2=bx+int(55*math.cos(ang))
            dy2=by+int(55*math.sin(ang))
            ds=PBF_SM.render(d,True,col)
            surf.blit(ds,(dx2-ds.get_width()//2,dy2-ds.get_height()//2))

    # Stick figure on left
    sx,sy=200,PB_H//2
    t2=t*0.12
    pygame.draw.circle(surf,PB_WHITE,(sx,sy-28),12,2)
    pygame.draw.line(surf,PB_WHITE,(sx,sy-16),(sx,sy+10),2)
    lsw=int(10*math.sin(t2))
    pygame.draw.line(surf,PB_WHITE,(sx,sy+10),(sx-lsw,sy+32),2)
    pygame.draw.line(surf,PB_WHITE,(sx,sy+10),(sx+lsw,sy+32),2)
    pygame.draw.line(surf,PB_WHITE,(sx,sy-6),(sx-14,sy+4+lsw),2)
    pygame.draw.line(surf,PB_WHITE,(sx,sy-6),(sx+14,sy+4-lsw),2)

def draw_pb_end(surf, won):
    surf.fill((0,0,0))
    if won:
        t1=PBF_LG.render("π IS TAMED!", True, PB_GREEN)
        t2=PBF_MD.render("π has submitted... and joins your toolkit.", True, PB_GOLD)
        t3=PBF_SM.render("You can now use π in calculations! (press P)", True, PB_CYAN)
    else:
        t1=PBF_LG.render("π REMAINS FREE!", True, PB_RED)
        t2=PBF_MD.render("The irrational number escapes your grasp.", True, PB_ORANGE)
        t3=PBF_SM.render("Returning to calculator...", True, PB_GRAY)
    surf.blit(t1,(PB_W//2-t1.get_width()//2,PB_H//2-110))
    surf.blit(t2,(PB_W//2-t2.get_width()//2,PB_H//2-40))
    surf.blit(t3,(PB_W//2-t3.get_width()//2,PB_H//2+30))

def draw_pb_background(surf):
    for row in range(0,PB_H,4):
        frac=row/PB_H
        r=int(8+10*frac); g=int(5+4*frac); b=int(20+18*frac)
        pygame.draw.line(surf,(r,g,b),(0,row),(PB_W,row))
    for s in pi_bg_syms:
        s.update(); s.draw(surf)
    pygame.draw.line(surf,(38,32,65),(PB_W//2,0),(PB_W//2,PB_H),1)

def is_pi_approx(expr_str):
    """Check if the expression is close enough to π to trigger battle."""
    # Direct string match
    clean = expr_str.strip().replace(" ","")
    for approx in PI_APPROX_EXPRS:
        if clean == approx.replace(" ",""):
            return True
    # Evaluate and check closeness
    try:
        val = eval(clean)
        if abs(val - PI_VALUE) < 0.01:
            return True
    except Exception:
        pass
    return False

# ═══════════════════════════════════════════════════════════
#  END PI BATTLE SYSTEM
# ═══════════════════════════════════════════════════════════

# ── evaluate main expression ───────────────────────────────
def evaluate():
    global result_text, pb_state, pi_battle_done, pi_unlocked
    if not placed:
        return
    raw = "".join(s["key"] for s in placed
                  if s["key"] not in ("=", "sg", "del", "C"))
    raw = raw.replace("%", "/100")

    # Check for pi approximation BEFORE evaluating
    if not pi_battle_done and is_pi_approx(raw):
        start_pi_battle()
        return   # don't evaluate — go to battle!

    try:
        ans = eval(raw)
        if isinstance(ans, float):
            result_text = f"{ans:.8f}".rstrip("0").rstrip(".")
        else:
            result_text = str(ans)
        burst(int(DX+DW//2), int(DY+DH//2), GREEN, n=24)
    except ZeroDivisionError:
        result_text = "DIV/0"
        burst(int(DX+DW//2), int(DY+DH//2), RED, n=14)
    except Exception:
        result_text = "ERR"
        burst(int(DX+DW//2), int(DY+DH//2), RED, n=10)

# ── draw display ───────────────────────────────────────────
def draw_display(surf, fig):
    pygame.draw.rect(surf, DISP_BG,     (DX, DY, DW, DH), border_radius=10)
    pygame.draw.rect(surf, DISP_BORDER, (DX, DY, DW, DH), 2, border_radius=10)

    for row in range(DY+3, DY+DH-3, 5):
        pygame.draw.line(surf, (0, 6, 3), (DX+3, row), (DX+DW-3, row))

    pygame.draw.line(surf, (35, 95, 52),
                     (DX+8, WORLD_FLOOR+2), (DX+DW-8, WORLD_FLOOR+2), 1)

    if result_text:
        rs = F_BIG.render("= " + result_text, True, GREEN)
        surf.blit(rs, (DX + DW - rs.get_width() - 10, DY + 8))

    lbl = F_TINY.render("DISPLAY  —  FIGURE'S WORLD", True, (35, 88, 50))
    surf.blit(lbl, (DX+4, DY+DH-14))

    draw_placed(surf)
    fig.draw(surf)

# ── draw calculator ────────────────────────────────────────
def draw_calc(surf):
    pygame.draw.rect(surf, CALC_BODY,   (CX, CY, CW, CH), border_radius=18)
    pygame.draw.rect(surf, CALC_BORDER, (CX, CY, CW, CH), 3, border_radius=18)

    brand = F_XS.render("DIGIT KEEPER  v2.2 — Sigma & Integral", True, GRAY)
    surf.blit(brand, (CX + CW//2 - brand.get_width()//2, CY + 8))

    for btn in BUTTONS:
        r  = btn["rect"]
        fl = btn["flash"]
        bg = btn["bg"]
        if fl > 0:
            t  = fl / 22.0
            bg = tuple(min(255, int(c + (255-c)*t*0.65)) for c in bg)
            btn["flash"] -= 1
        pygame.draw.rect(surf, bg, r, border_radius=7)
        pygame.draw.rect(surf, CALC_BORDER, r, 1, border_radius=7)

        lc = sym_color(btn["key"])
        ls = F_SM.render(btn["text"], True, lc)
        surf.blit(ls, (r.centerx - ls.get_width()//2,
                       r.centery - ls.get_height()//2))

    # Key hint labels on Sigma/Integral buttons
    for btn in BUTTONS:
        if btn["key"] == "SIG":
            h = F_TINY.render("[S]", True, (40,100,100))
            surf.blit(h, (btn["rect"].x+4, btn["rect"].y+3))
        elif btn["key"] == "INT":
            h = F_TINY.render("[I]", True, (60,60,160))
            surf.blit(h, (btn["rect"].x+4, btn["rect"].y+3))

# ── right panel ────────────────────────────────────────────
def draw_panel(surf, fig):
    px, py = CX + CW + 22, CY

    surf.blit(F_MED.render("DIGIT KEEPER 2", True, CYAN), (px, py)); py += 32
    surf.blit(F_XS.render("Pick up a symbol, walk, SPACE to place!", True, GRAY),
              (px, py)); py += 40

    # Held
    pygame.draw.rect(surf, DARK, (px, py, 350, 86), border_radius=10)
    pygame.draw.rect(surf, CALC_BORDER, (px, py, 350, 86), 2, border_radius=10)
    surf.blit(F_XS.render("HOLDING:", True, GRAY), (px+10, py+8))
    if fig.held_key:
        big = F_GIANT.render(fig.held_text, True, sym_color(fig.held_key))
        surf.blit(big, (px+175 - big.get_width()//2,
                        py+43  - big.get_height()//2))
    else:
        nd = F_SM.render("nothing", True, (50, 50, 74))
        surf.blit(nd, (px+175 - nd.get_width()//2, py+36))
    py += 100

    # Expression
    pygame.draw.rect(surf, DARK, (px, py, 350, 42), border_radius=7)
    pygame.draw.rect(surf, CALC_BORDER, (px, py, 350, 42), 1, border_radius=7)
    surf.blit(F_XS.render("EXPRESSION:", True, GRAY), (px+8, py+5))
    expr_str = " ".join(s["text"] for s in placed) if placed else "—"
    # Trim if too long
    if len(expr_str) > 30:
        expr_str = "..." + expr_str[-27:]
    surf.blit(F_SM.render(expr_str, True, GREEN), (px+8, py+20))
    py += 54

    if result_text:
        pygame.draw.rect(surf, DARK, (px, py, 350, 42), border_radius=7)
        pygame.draw.rect(surf, CALC_BORDER, (px, py, 350, 42), 1, border_radius=7)
        surf.blit(F_XS.render("RESULT:", True, GRAY), (px+8, py+5))
        surf.blit(F_SM.render(result_text, True, LIME), (px+8, py+20))
        py += 54

    # Controls
    py += 6
    surf.blit(F_SM.render("CONTROLS", True, CYAN), (px, py)); py += 24

    controls = [
        ("0–9",       "Pick up digit"),
        ("+ - * /",   "Pick up operator"),
        ("S",         "Pick up Sigma  Σ"),
        ("I",         "Pick up Integral  ∫"),
        ("P",         "Pick up π  (unlock by battling!)"),
        ("← → A D",  "Walk"),
        ("↑ / W",     "Jump"),
        ("SPACE",     "Place symbol here"),
        ("BACKSPACE", "Pick up nearest symbol"),
        ("ENTER",     "Evaluate  (try 22/7!)"),
        ("C",         "Clear all"),
    ]
    for k, d in controls:
        col = TEAL   if k == "S" else \
              INDIGO if k == "I" else YELLOW
        surf.blit(F_XS.render(k,       True, col),   (px,     py))
        surf.blit(F_XS.render("— "+d,  True, WHITE), (px+115, py))
        py += 18

    # Special legend
    py += 8
    pygame.draw.rect(surf, DARK, (px, py, 350, 78), border_radius=7)
    pygame.draw.rect(surf, CALC_BORDER, (px, py, 350, 78), 1, border_radius=7)
    surf.blit(F_XS.render("SPECIAL FUNCTIONS", True, GRAY), (px+8, py+5))
    surf.blit(F_XS.render("S — Sigma: sum f(n) from n=a to n=b", True, TEAL),   (px+8, py+22))
    surf.blit(F_XS.render("I — Integral: area under f(x) from a to b", True, INDIGO), (px+8, py+38))
    pi_col = PB_GOLD if pi_unlocked else GRAY
    pi_msg = "P — π  UNLOCKED! Use it freely." if pi_unlocked else \
             "P — π  LOCKED. Enter 22/7 then ENTER to fight!"
    surf.blit(F_XS.render(pi_msg, True, pi_col), (px+8, py+54))


def draw_bg(surf):
    surf.fill(BG)
    for gx in range(0, W, 30):
        pygame.draw.line(surf, (19, 19, 32), (gx, 0), (gx, H))
    for gy in range(0, H, 30):
        pygame.draw.line(surf, (19, 19, 32), (0, gy), (W, gy))


# ── main loop ──────────────────────────────────────────────
fig = Figure()

running = True
while running:
    clock.tick(60)

    # ════════════════════════════════════════
    #  PI BATTLE ACTIVE — handle separately
    # ════════════════════════════════════════
    if pb_state is not None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if pb_state == "intro":
                    if event.key == pygame.K_SPACE and pb_intro_t >= 450:
                        pb_state = "fight"
                elif pb_state == "fight":
                    if event.key == pygame.K_ESCAPE:
                        # Give up — return to calc, battle stays done (failed)
                        pb_state = None
                        pi_battle_done = True
                elif pb_state in ("win","lose"):
                    pass  # auto-returns after pb_post_t

        keys = pygame.key.get_pressed()

        if pb_state == "intro":
            pb_intro_t += 1
            draw_pb_background(screen)
            draw_pb_intro(screen, pb_intro_t)

        elif pb_state == "fight":
            pb_player.handle_input(keys)
            pb_player.update()

            if keys[pygame.K_SPACE]:
                shot = pb_player.shoot()
                if shot: pb_shots.append(shot)

            pb_boss.update(pb_player.y)
            pb_boss.shoot_timer += 1
            if pb_boss.shoot_timer >= pb_boss.shoot_rate:
                pb_boss.shoot_timer = 0
                pb_shots.extend(pb_boss.shoot(pb_player.x, pb_player.y))

            for s in pb_shots: s.update()

            # Collisions
            for s in [ss for ss in pb_shots if ss.owner=="player" and ss.alive]:
                if s.rect().colliderect(pb_boss.rect()):
                    pb_boss.take_damage(s.damage)
                    pb_player.score += s.damage
                    s.alive = False
                    pb_trigger_flash(PB_RED, 40)

            for s in [ss for ss in pb_shots if ss.owner=="enemy" and ss.alive]:
                if s.rect().colliderect(pb_player.rect()):
                    pb_player.take_damage(s.damage)
                    s.alive = False
                    pb_trigger_flash(PB_WHITE, 30)

            pb_shots = [s for s in pb_shots if s.alive]
            pb_upd_particles()

            if pb_boss.hp <= 0:
                pb_state = "win"
                pb_post_t = 180
                pi_battle_done = True
                pi_unlocked    = True
                pb_burst(int(pb_boss.x),int(pb_boss.y),PB_GOLD,n=50,
                         texts=["π","3.14","tamed!"])

            if pb_player.hp <= 0:
                pb_state = "lose"
                pb_post_t = 180
                pi_battle_done = True   # won't fight again even on lose

            # Draw
            draw_pb_background(screen)
            pb_boss.draw(screen)
            pb_player.draw(screen)
            for s in pb_shots: s.draw(screen)
            pb_draw_particles(screen)
            draw_pb_hud(screen, pb_player, pb_boss)

            if pb_flash > 0:
                fs = pygame.Surface((PB_W,PB_H), pygame.SRCALPHA)
                fs.fill((*pb_flash_col, min(160, pb_flash*2)))
                screen.blit(fs,(0,0))
                pb_flash = max(0, pb_flash-5)

        elif pb_state in ("win","lose"):
            pb_post_t -= 1
            draw_pb_end(screen, pb_state == "win")
            pb_draw_particles(screen)
            if pb_post_t <= 0:
                pb_state = None   # return to calculator

        pygame.display.flip()
        continue   # skip normal calc loop this frame

    # ════════════════════════════════════════
    #  NORMAL CALCULATOR MODE
    # ════════════════════════════════════════
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            k = event.key
            u = event.unicode

            # ── popup is open ──────────────────────────────
            if popup["mode"]:
                if k == pygame.K_ESCAPE:
                    close_popup()
                elif k == pygame.K_TAB:
                    popup_next_field()
                elif k == pygame.K_BACKSPACE:
                    popup_backspace()
                elif k == pygame.K_RETURN:
                    try:
                        val, lbl = popup_compute()
                        popup["result"] = val
                        mode = popup["mode"]
                        close_popup()
                        col = TEAL if mode == "sigma" else INDIGO
                        fig.place_value(val, lbl, col)
                        burst(int(fig.x), int(fig.y)-40, col, n=20)
                    except Exception as ex:
                        popup["error"] = str(ex)
                elif u and (u.isprintable()):
                    popup_type_char(u)

            # ── normal mode ────────────────────────────────
            else:
                if k == pygame.K_ESCAPE:
                    running = False

                elif u in "0123456789":
                    fig.pick(u, u)
                elif u == "+":
                    fig.pick("+", "+")
                elif u == "-":
                    fig.pick("-", "-")
                elif u == "*":
                    fig.pick("*", "×")
                elif u == "/":
                    fig.pick("/", "÷")
                elif u == "=":
                    fig.pick("=", "=")
                elif u == ".":
                    fig.pick(".", ".")
                elif u == "%":
                    fig.pick("%", "%")
                elif u in ("s", "S"):
                    fig.pick("SIG", "Σ")
                elif u in ("i", "I"):
                    fig.pick("INT", "∫")

                # P = pick up π (only if unlocked)
                elif u in ("p", "P"):
                    if pi_unlocked:
                        fig.pick("3.14159265358979", "π")
                        burst(int(fig.x), int(fig.y)-40, PB_GOLD, n=20)
                    else:
                        # Tease — show locked message
                        burst(int(DX+DW//2), int(DY+10), PB_ORANGE, n=8)
                        result_text = "Defeat π first! (try 22/7 then ENTER)"

                elif k == pygame.K_SPACE:
                    fig.place()
                elif k == pygame.K_BACKSPACE:
                    fig.delete_nearest()
                elif k == pygame.K_RETURN:
                    evaluate()
                elif u in ("c", "C"):
                    placed.clear()
                    result_text = ""
                    fig.drop()
                    burst(int(DX+DW//2), int(DY+DH//2), RED, n=16)

    keys = pygame.key.get_pressed()
    fig.handle_keys(keys)
    fig.update()
    update_placed()
    upd_px()

    draw_bg(screen)
    draw_calc(screen)
    draw_display(screen, fig)
    draw_px(screen)
    draw_panel(screen, fig)
    draw_popup(screen)

    # π unlocked badge
    if pi_unlocked:
        badge = F_SM.render("π UNLOCKED — press P to pick up π", True, PB_GOLD)
        screen.blit(badge, (DX + DW//2 - badge.get_width()//2, DY - 18))
    elif pi_battle_done:
        badge = F_XS.render("π escaped — P key locked", True, GRAY)
        screen.blit(badge, (DX + DW//2 - badge.get_width()//2, DY - 16))

    pygame.display.flip()

pygame.quit()
sys.exit()
