"""
DIGIT KEEPER 2  —  The Figure Places the Numbers
=================================================
The stick figure lives INSIDE the calculator display.
Walk it left and right, pick up a symbol, then walk
to where you want it and DROP it to place it in the expression.

Run:   python3 digit_keeper2.py

CONTROLS
  ←  /  A          Walk left
  →  /  D          Walk right
  ↑  /  W          Jump
  0–9               Pick up that digit
  +  -  *  /        Pick up that operator
  =                 Pick up the equals sign
  .                 Pick up decimal point
  SPACE             Place / drop held symbol at current position
  BACKSPACE         Delete symbol nearest the figure
  C                 Clear entire expression
  ENTER             Evaluate the expression
  ESC               Quit
"""

import pygame
import math
import random
import sys

pygame.init()

W, H = 1100, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Digit Keeper 2 — Display World")
clock = pygame.time.Clock()

# ── fonts ──────────────────────────────────────────────────
def make_font(size, bold=False):
    for name in ["Consolas", "Courier New", None]:
        try:    return pygame.font.SysFont(name, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

F_GIANT = make_font(80, bold=True)
F_BIG   = make_font(46, bold=True)
F_MED   = make_font(30, bold=True)
F_SM    = make_font(20, bold=True)
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

# ── calculator geometry ────────────────────────────────────
CX, CY = 50, 20
CW, CH = 500, 680

# The display — tall so the figure has room
DX = CX + 16
DY = CY + 32
DW = CW - 32
DH = 240        # tall display — figure lives here

# Display world bounds for the figure
WORLD_LEFT  = DX + 10
WORLD_RIGHT = DX + DW - 10
WORLD_FLOOR = DY + DH - 10   # figure's feet rest here (or on symbols)
WORLD_CEIL  = DY + 8         # figure can't go above this

# Buttons below display
BAY     = DY + DH + 18
BTW     = 106
BTH     = 58
BTGAP   = 7

BUTTON_DEFS = [
    ("C",   "C",   0, 0, BTN_CLR),
    ("sg",  "+/-", 1, 0, BTN_OP),
    ("%",   "%",   2, 0, BTN_OP),
    ("/",   "÷",   3, 0, BTN_OP),
    ("7",   "7",   0, 1, BTN_NUM),
    ("8",   "8",   1, 1, BTN_NUM),
    ("9",   "9",   2, 1, BTN_NUM),
    ("*",   "×",   3, 1, BTN_OP),
    ("4",   "4",   0, 2, BTN_NUM),
    ("5",   "5",   1, 2, BTN_NUM),
    ("6",   "6",   2, 2, BTN_NUM),
    ("-",   "−",   3, 2, BTN_OP),
    ("1",   "1",   0, 3, BTN_NUM),
    ("2",   "2",   1, 3, BTN_NUM),
    ("3",   "3",   2, 3, BTN_NUM),
    ("+",   "+",   3, 3, BTN_OP),
    ("0",   "0",   0, 4, BTN_NUM),
    (".",   ".",   1, 4, BTN_NUM),
    ("=",   "=",   2, 4, BTN_EQ),
    ("del", "⌫",   3, 4, BTN_CLR),
]

def btn_rect(col, row):
    return pygame.Rect(
        CX + 16 + col * (BTW + BTGAP),
        BAY      + row * (BTH + BTGAP),
        BTW, BTH
    )

BUTTONS = [{"key": k, "text": t, "rect": btn_rect(c, r), "bg": bg, "flash": 0}
           for k, t, c, r, bg in BUTTON_DEFS]

# symbol colors
def sym_color(key):
    if key in ("+", "+"): return GREEN
    if key == "-":        return CYAN
    if key == "*":        return ORANGE
    if key == "/":        return PURPLE
    if key == "=":        return LIME
    if key in ("C","del","DEL"): return RED
    if key == "%":        return PINK
    if key in ("sg","+/-"): return YELLOW
    if key == ".":        return WHITE
    return YELLOW   # digits

# ── particles ──────────────────────────────────────────────
_px = []

def burst(x, y, col, n=10):
    for _ in range(n):
        _px.append({"x": float(x), "y": float(y),
                    "vx": random.uniform(-3, 3),
                    "vy": random.uniform(-4.5, -0.3),
                    "col": col, "life": random.randint(28, 50), "ml": 45,
                    "r": random.randint(3, 6)})

def upd_px():
    for p in _px: p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["vy"]+=0.14; p["life"]-=1
    _px[:] = [p for p in _px if p["life"] > 0]

def draw_px(surf):
    for p in _px:
        a = p["life"] / p["ml"]
        c = tuple(min(255, int(ch*a)) for ch in p["col"])
        pygame.draw.circle(surf, c, (int(p["x"]), int(p["y"])),
                           max(1, int(p["r"]*a)))

# ── placed symbols in the display ─────────────────────────
# Each placed symbol: {x (centre), text, key, landed}
placed = []     # list of dicts, in display order
result_text = ""   # shown when = is evaluated

SLOT_SIZE   = 36   # width each placed symbol takes
SLOT_SPACING = 38

def get_slot_x(index):
    """X centre of slot index, starting from left of display."""
    return WORLD_LEFT + 20 + index * SLOT_SPACING

def find_insert_index(fig_x):
    """Return the index at which to insert a new symbol given figure x."""
    for i, sym in enumerate(placed):
        if fig_x < sym["x"]:
            return i
    return len(placed)

def find_nearest_index(fig_x):
    """Return index of placed symbol nearest figure x, or None."""
    if not placed:
        return None
    best_i = 0
    best_d = abs(placed[0]["x"] - fig_x)
    for i, sym in enumerate(placed):
        d = abs(sym["x"] - fig_x)
        if d < best_d:
            best_d = d
            best_i = i
    return best_i

def reflow():
    """Re-space all placed symbols evenly from left."""
    for i, sym in enumerate(placed):
        sym["x"] = float(get_slot_x(i))

# ── figure ─────────────────────────────────────────────────
class Figure:
    SPEED  = 3.8
    GRAV   = 0.55
    JUMP_V = -11.0

    def __init__(self):
        self.x  = float(DX + DW // 2)
        self.y  = float(WORLD_FLOOR)    # feet
        self.vx = 0.0
        self.vy = 0.0
        self.grounded   = True
        self.j_held     = False
        self.walk_t     = 0.0
        self.facing     = 1

        self.held_key   = None   # internal key e.g. "7", "+", "="
        self.held_text  = None   # display text e.g. "7", "+", "="
        self.held_scale = 1.0
        self.held_col   = WHITE

        self.anim_place    = 0
        self.anim_pickup   = 0
        self.anim_celebrate= 0
        self.anim_blink    = 0

    def pick(self, key, text):
        self.held_key   = key
        self.held_text  = text
        self.held_col   = sym_color(key)
        self.held_scale = 1.6
        self.anim_pickup = 18
        burst(int(self.x), int(self.y)-40, self.held_col, n=14)

    def drop(self):
        """Drop/clear held symbol without placing."""
        if self.held_key:
            burst(int(self.x), int(self.y)-30, RED, n=8)
        self.held_key  = None
        self.held_text = None

    def place(self):
        """Place held symbol into the expression at figure's position."""
        global result_text
        if self.held_key is None:
            return

        result_text = ""   # clear any previous result when editing
        idx = find_insert_index(self.x)
        placed.insert(idx, {
            "x":    float(get_slot_x(idx)),
            "text": self.held_text,
            "key":  self.held_key,
            "scale": 1.4,   # pop scale
            "vy": -6.0,     # little bounce up when placed
            "grounded": False,
        })
        reflow()

        col = self.held_col
        burst(int(self.x), int(self.y)-30, col, n=16)
        self.anim_place    = 18
        self.anim_celebrate= 38

        self.held_key  = None
        self.held_text = None

    def delete_nearest(self):
        """Delete the placed symbol nearest the figure."""
        global result_text
        idx = find_nearest_index(self.x)
        if idx is not None:
            burst(int(placed[idx]["x"]), int(WORLD_FLOOR - 30), RED, n=10)
            placed.pop(idx)
            reflow()
            result_text = ""

    def handle_keys(self, keys):
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.vx = -self.SPEED; self.facing = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx =  self.SPEED; self.facing =  1
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
        self.x += self.vx
        self.x  = max(float(WORLD_LEFT), min(float(WORLD_RIGHT), self.x))

        self.vy += self.GRAV
        self.y  += self.vy

        # Floor
        self.grounded = False
        if self.vy >= 0 and self.y >= WORLD_FLOOR:
            self.y = float(WORLD_FLOOR)
            self.vy = 0.0
            self.grounded = True

        # Ceiling
        if self.y < WORLD_CEIL + 44:
            self.y  = float(WORLD_CEIL + 44)
            self.vy = max(0.0, self.vy)

        # Scale bounce for held symbol
        if self.held_scale > 1.0:
            self.held_scale = max(1.0, self.held_scale - 0.06)

        # Timers
        if self.anim_place     > 0: self.anim_place     -= 1
        if self.anim_pickup    > 0: self.anim_pickup     -= 1
        if self.anim_celebrate > 0: self.anim_celebrate  -= 1
        if self.anim_blink     > 0: self.anim_blink      -= 1
        if random.random() < 0.004: self.anim_blink = 9

    def draw(self, surf):
        x  = int(self.x)
        fy = int(self.y)       # feet
        hy = fy - 36           # head centre

        cel  = self.anim_celebrate > 0
        pick = self.anim_pickup    > 0

        # shadow
        pygame.draw.ellipse(surf, (20, 45, 25), (x-12, fy+1, 24, 6))

        # head
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

        # body
        pygame.draw.line(surf, WHITE, (x, hy+11), (x, fy-10), 2)

        # legs
        sw = int(10*math.sin(self.walk_t)) if abs(self.vx) > 0.2 else 0
        pygame.draw.line(surf, WHITE, (x, fy-10), (x-sw, fy), 2)
        pygame.draw.line(surf, WHITE, (x, fy-10), (x+sw, fy), 2)

        # arms + held symbol
        if self.held_key:
            # Arms raised holding symbol above head
            lift = -14 if not cel else -18 + int(4*math.sin(self.walk_t*3))
            pygame.draw.line(surf, WHITE, (x, hy+13), (x-17, hy+lift), 2)
            pygame.draw.line(surf, WHITE, (x, hy+13), (x+17, hy+lift), 2)

            # glow halo
            hcol = self.held_col
            gs = pygame.Surface((70, 70), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*hcol, 50), (35, 35), 32)
            surf.blit(gs, (x-35, hy-68))

            # the symbol itself
            sc = self.held_scale
            s  = F_BIG.render(self.held_text, True, hcol)
            if sc != 1.0:
                nw, nh = int(s.get_width()*sc), int(s.get_height()*sc)
                s = pygame.transform.scale(s, (nw, nh))
            surf.blit(s, (x - s.get_width()//2, hy - 72 - s.get_height()//2))

            # sparkles when just picked up
            if cel or pick:
                for i in range(5):
                    ang = self.walk_t*4 + i*2*math.pi/5
                    sx2 = x + int(28*math.cos(ang))
                    sy2 = hy - 68 + int(10*math.sin(ang))
                    pygame.draw.circle(surf, hcol, (sx2, sy2), 3)

            # "SPACE to place" hint above symbol
            hint = F_TINY.render("SPACE = place here", True, hcol)
            surf.blit(hint, (x - hint.get_width()//2, hy - 100))

        elif self.anim_place > 0:
            # Just placed — arms out celebrating
            t2 = self.walk_t * 4
            pygame.draw.line(surf, WHITE, (x, hy+13),
                             (x-17, hy + int(5*math.sin(t2))), 2)
            pygame.draw.line(surf, WHITE, (x, hy+13),
                             (x+17, hy + int(5*math.sin(t2+1))), 2)
        else:
            # Normal walk/idle arms
            sw2 = int(8*math.sin(self.walk_t+math.pi)) if abs(self.vx)>0.2 else 0
            pygame.draw.line(surf, WHITE, (x, hy+13), (x-14, fy-20+sw2), 2)
            pygame.draw.line(surf, WHITE, (x, hy+13), (x+14, fy-20-sw2), 2)

        # insertion cursor — show where symbol will land
        if self.held_key:
            idx = find_insert_index(self.x)
            cx2 = get_slot_x(idx)
            # draw a blinking caret on the floor
            if (pygame.time.get_ticks() // 300) % 2 == 0:
                pygame.draw.line(surf, self.held_col,
                                 (int(cx2), WORLD_FLOOR - 28),
                                 (int(cx2), WORLD_FLOOR - 4), 2)
                pygame.draw.polygon(surf, self.held_col, [
                    (int(cx2)-5, WORLD_FLOOR - 6),
                    (int(cx2)+5, WORLD_FLOOR - 6),
                    (int(cx2),   WORLD_FLOOR),
                ])


# ── update placed symbols (bounce-in animation) ────────────
def update_placed():
    for sym in placed:
        if not sym.get("grounded", True):
            sym["y"] = sym.get("y", float(WORLD_FLOOR - 24)) + sym["vy"]
            sym["vy"] = sym.get("vy", 0) + 0.5
            if sym.get("y", WORLD_FLOOR) >= WORLD_FLOOR - 24:
                sym["y"] = float(WORLD_FLOOR - 24)
                sym["vy"] = 0.0
                sym["grounded"] = True
        if sym.get("scale", 1.0) > 1.0:
            sym["scale"] = max(1.0, sym["scale"] - 0.06)


def draw_placed(surf):
    """Draw placed symbols sitting on the display floor."""
    for i, sym in enumerate(placed):
        sx  = int(sym["x"])
        sy  = int(sym.get("y", float(WORLD_FLOOR - 24)))
        sc  = sym.get("scale", 1.0)
        col = sym_color(sym["key"])

        s = F_MED.render(sym["text"], True, col)
        if sc != 1.0:
            nw, nh = int(s.get_width()*sc), int(s.get_height()*sc)
            s = pygame.transform.scale(s, (nw, nh))
        surf.blit(s, (sx - s.get_width()//2, sy - s.get_height()//2))

        # small underline below each symbol
        pygame.draw.line(surf, tuple(c//2 for c in col),
                         (sx-14, WORLD_FLOOR - 4),
                         (sx+14, WORLD_FLOOR - 4), 1)


# ── expression evaluation ──────────────────────────────────
def evaluate():
    global result_text
    if not placed:
        return

    # Build expression from placed symbols
    raw = "".join(sym["key"] for sym in placed
                  if sym["key"] not in ("=", "sg", "del", "C"))
    raw = raw.replace("%", "/100")

    try:
        ans = eval(raw)
        if isinstance(ans, float):
            s = f"{ans:.8f}".rstrip("0").rstrip(".")
        else:
            s = str(ans)
        result_text = s
        burst(int(DX + DW//2), int(DY + DH//2), GREEN, n=24)
    except ZeroDivisionError:
        result_text = "DIV/0!"
        burst(int(DX + DW//2), int(DY + DH//2), RED, n=14)
    except Exception:
        result_text = "ERR"
        burst(int(DX + DW//2), int(DY + DH//2), RED, n=10)


# ── draw the display screen ────────────────────────────────
def draw_display(surf, fig):
    # Background
    pygame.draw.rect(surf, DISP_BG,
                     (DX, DY, DW, DH), border_radius=10)
    pygame.draw.rect(surf, DISP_BORDER,
                     (DX, DY, DW, DH), 2, border_radius=10)

    # Scanlines
    for row in range(DY+3, DY+DH-3, 5):
        pygame.draw.line(surf, (0, 6, 3),
                         (DX+3, row), (DX+DW-3, row))

    # Floor line
    pygame.draw.line(surf, (35, 95, 52),
                     (DX+8, WORLD_FLOOR+2),
                     (DX+DW-8, WORLD_FLOOR+2), 1)

    # Result text (floats at top-right)
    if result_text:
        rs = F_BIG.render("= " + result_text, True, GREEN)
        surf.blit(rs, (DX + DW - rs.get_width() - 10, DY + 8))

    # "display world" label
    lbl = F_TINY.render("DISPLAY  —  FIGURE'S WORLD", True, (35, 88, 50))
    surf.blit(lbl, (DX+4, DY+DH-14))

    # Placed symbols
    draw_placed(surf)

    # Figure (drawn inside display clip)
    fig.draw(surf)


# ── draw the calculator shell + buttons ───────────────────
def draw_calc(surf):
    pygame.draw.rect(surf, CALC_BODY,   (CX, CY, CW, CH), border_radius=18)
    pygame.draw.rect(surf, CALC_BORDER, (CX, CY, CW, CH), 3, border_radius=18)

    brand = F_XS.render("DIGIT KEEPER  v2.1", True, GRAY)
    surf.blit(brand, (CX + CW//2 - brand.get_width()//2, CY + 10))

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


# ── right info panel ───────────────────────────────────────
def draw_panel(surf, fig):
    px, py = CX + CW + 26, CY

    surf.blit(F_MED.render("DIGIT KEEPER 2", True, CYAN), (px, py)); py += 34
    surf.blit(F_XS.render("Pick up a symbol, walk, drop it!", True, GRAY),
              (px, py)); py += 44

    # Held symbol box
    pygame.draw.rect(surf, DARK, (px, py, 340, 90), border_radius=10)
    pygame.draw.rect(surf, CALC_BORDER, (px, py, 340, 90), 2, border_radius=10)
    surf.blit(F_XS.render("HOLDING:", True, GRAY), (px+10, py+8))
    if fig.held_key:
        big = F_GIANT.render(fig.held_text, True, sym_color(fig.held_key))
        surf.blit(big, (px+170 - big.get_width()//2,
                        py+45  - big.get_height()//2))
    else:
        nd = F_SM.render("nothing", True, (52, 52, 76))
        surf.blit(nd, (px+170 - nd.get_width()//2, py+38))
    py += 106

    # Expression preview
    pygame.draw.rect(surf, DARK, (px, py, 340, 44), border_radius=7)
    pygame.draw.rect(surf, CALC_BORDER, (px, py, 340, 44), 1, border_radius=7)
    surf.blit(F_XS.render("EXPRESSION:", True, GRAY), (px+8, py+6))
    expr_str = " ".join(s["text"] for s in placed) if placed else "—"
    surf.blit(F_SM.render(expr_str, True, GREEN), (px+8, py+22))
    py += 56

    if result_text:
        pygame.draw.rect(surf, DARK, (px, py, 340, 44), border_radius=7)
        pygame.draw.rect(surf, CALC_BORDER, (px, py, 340, 44), 1, border_radius=7)
        surf.blit(F_XS.render("RESULT:", True, GRAY), (px+8, py+6))
        surf.blit(F_SM.render(result_text, True, LIME), (px+8, py+22))
        py += 56

    # Controls
    py += 8
    surf.blit(F_SM.render("CONTROLS", True, CYAN), (px, py)); py += 26
    for k, d in [
        ("0–9",          "Pick up digit"),
        ("+ - * /",      "Pick up operator"),
        ("=",            "Pick up equals"),
        ("← → / A D",   "Walk"),
        ("↑ / W",        "Jump"),
        ("SPACE",        "Place symbol here"),
        ("BACKSPACE",    "Delete nearest symbol"),
        ("ENTER",        "Evaluate expression"),
        ("C",            "Clear all"),
        ("ESC",          "Quit"),
    ]:
        surf.blit(F_XS.render(k,       True, YELLOW), (px,     py))
        surf.blit(F_XS.render("— "+d,  True, WHITE),  (px+130, py))
        py += 19

    py += 10
    tips = [
        "Walk between symbols to insert new ones!",
        "The caret shows where symbol will land.",
        "Build:  9  +  3  then press ENTER.",
        "Symbols bounce when placed!",
        "Delete nearest symbol with BACKSPACE.",
    ]
    tip = tips[(pygame.time.get_ticks()//3500) % len(tips)]
    surf.blit(F_XS.render("Tip: " + tip, True, (88, 148, 108)), (px, py))


# ── background ─────────────────────────────────────────────
def draw_bg(surf):
    surf.fill(BG)
    for gx in range(0, W, 30):
        pygame.draw.line(surf, (19, 19, 32), (gx, 0), (gx, H))
    for gy in range(0, H, 30):
        pygame.draw.line(surf, (19, 19, 32), (0, gy), (W, gy))


# ── key → (internal_key, display_text) ────────────────────
KEY_MAP = {
    pygame.K_0: ("0","0"), pygame.K_1: ("1","1"), pygame.K_2: ("2","2"),
    pygame.K_3: ("3","3"), pygame.K_4: ("4","4"), pygame.K_5: ("5","5"),
    pygame.K_6: ("6","6"), pygame.K_7: ("7","7"), pygame.K_8: ("8","8"),
    pygame.K_9: ("9","9"),
    pygame.K_PLUS:    ("+","+"),  pygame.K_EQUALS: ("+","+"),
    pygame.K_MINUS:   ("-","−"),
    pygame.K_SLASH:   ("/","÷"),
    pygame.K_ASTERISK:("*","×"),
    pygame.K_PERIOD:  (".","." ),
    pygame.K_RETURN:  None,   # evaluate
}

# ── main loop ──────────────────────────────────────────────
fig = Figure()

running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            k = event.key

            if k == pygame.K_ESCAPE:
                running = False

            # Pick up digit via number keys
            elif event.unicode in "0123456789":
                fig.pick(event.unicode, event.unicode)

            # Pick up operators
            elif event.unicode == "+":
                fig.pick("+", "+")
            elif event.unicode == "-":
                fig.pick("-", "−")
            elif event.unicode == "*":
                fig.pick("*", "×")
            elif event.unicode == "/":
                fig.pick("/", "÷")
            elif event.unicode == "=":
                fig.pick("=", "=")
            elif event.unicode == ".":
                fig.pick(".", ".")
            elif event.unicode == "%":
                fig.pick("%", "%")

            # Place
            elif k == pygame.K_SPACE:
                fig.place()

            # Delete nearest
            elif k == pygame.K_BACKSPACE:
                fig.delete_nearest()

            # Evaluate
            elif k == pygame.K_RETURN:
                evaluate()

            # Clear
            elif event.unicode in ("c", "C"):
                placed.clear()
                result_text = ""
                fig.drop()
                burst(int(DX + DW//2), int(DY + DH//2), RED, n=16)

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

    pygame.display.flip()

pygame.quit()
sys.exit()
