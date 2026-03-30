"""
DIGIT KEEPER 3
Run: python3 digit_keeper3.py

Walk the stick figure onto a calculator button, then press SPACE to press it.
The value appears on the display only when the figure physically presses the button.

Controls:
  A / D  or  Left / Right  -- Walk
  W      or  Up             -- Jump
  SPACE                     -- Press the button you stand on
  ESC                       -- Quit
"""

import pygame
import math
import random
import sys

pygame.init()

W, H = 1000, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Digit Keeper 3")
clock = pygame.time.Clock()

# ---------- fonts ----------
def make_font(size, bold=False):
    try:    return pygame.font.SysFont("consolas", size, bold=bold)
    except: return pygame.font.Font(None, size)

FONT_BIG = make_font(46, bold=True)
FONT_MED = make_font(28, bold=True)
FONT_SM  = make_font(20, bold=True)
FONT_XS  = make_font(14)

# ---------- colors ----------
COL_BG      = (13,  13,  22)
COL_CALC    = (26,  26,  40)
COL_BORDER  = (55,  55,  88)
COL_DISP    = (8,   20,  13)
COL_DBRDR   = (38, 130,  65)
COL_BNUM    = (36,  36,  56)
COL_BOP     = (54,  34,  72)
COL_BEQ     = (24,  82,  52)
COL_BCLR    = (82,  26,  36)
COL_WHITE   = (235, 240, 255)
COL_GREEN   = (65,  250, 125)
COL_CYAN    = (0,   205, 250)
COL_YELLOW  = (255, 225,  45)
COL_ORANGE  = (255, 145,  30)
COL_RED     = (255,  60,  60)
COL_PURPLE  = (170,  70, 250)
COL_GRAY    = (105, 105, 140)
COL_DARK    = (16,   16,  28)
COL_PINK    = (255, 105, 175)
COL_LIME    = (130, 255,  80)

# ---------- calculator layout ----------
# Calculator body
CX, CY = 55, 20
CW, CH = 480, 680

# Display screen (short — just shows numbers)
DX = CX + 18
DY = CY + 34
DW = CW - 36
DH = 68

# Buttons start here
BY0 = DY + DH + 16   # y of first button row top
BW  = 100             # button width
BH  = 58              # button height
BG  = 7               # gap between buttons

# Figure physical constants
FIG_HALF  = 12   # half-width for x collision
FIG_FEET  = 44   # distance from head-top to feet

# The absolute minimum y the figure's FEET can be
# (just below the display screen so figure can't float above buttons)
MIN_FEET_Y = DY + DH + FIG_FEET + 2

# Calculator floor (feet land here if between buttons)
MAX_FEET_Y = CY + CH - 6

# ---------- button definitions ----------
# (internal_label, display_text, col, row, bg_color)
BTN_DEFS = [
    ("C",   "C",   0, 0, COL_BCLR),
    ("sg",  "+/-", 1, 0, COL_BOP),
    ("%",   "%",   2, 0, COL_BOP),
    ("/",   "÷",   3, 0, COL_BOP),
    ("7",   "7",   0, 1, COL_BNUM),
    ("8",   "8",   1, 1, COL_BNUM),
    ("9",   "9",   2, 1, COL_BNUM),
    ("*",   "×",   3, 1, COL_BOP),
    ("4",   "4",   0, 2, COL_BNUM),
    ("5",   "5",   1, 2, COL_BNUM),
    ("6",   "6",   2, 2, COL_BNUM),
    ("-",   "-",   3, 2, COL_BOP),
    ("1",   "1",   0, 3, COL_BNUM),
    ("2",   "2",   1, 3, COL_BNUM),
    ("3",   "3",   2, 3, COL_BNUM),
    ("+",   "+",   3, 3, COL_BOP),
    ("0",   "0",   0, 4, COL_BNUM),
    (".",   ".",   1, 4, COL_BNUM),
    ("=",   "=",   2, 4, COL_BEQ),
    ("del", "<",   3, 4, COL_BCLR),
]

# Colour each button label gets when drawn
def btn_label_color(key):
    if key in ("C", "del"):          return COL_RED
    if key in ("/", "*", "-", "+",
               "%", "sg"):           return COL_CYAN
    if key == "=":                   return COL_LIME
    return COL_YELLOW   # digits and dot

# Build button objects
buttons = []
for key, text, col, row, bg in BTN_DEFS:
    rx = CX + 18 + col * (BW + BG)
    ry = BY0     + row * (BH + BG)
    buttons.append({
        "key":   key,
        "text":  text,
        "rect":  pygame.Rect(rx, ry, BW, BH),
        "bg":    bg,
        "flash": 0,
    })

# Verify all button tops are reachable (>= MIN_FEET_Y)
print("--- geometry check ---")
for row in range(5):
    ry = BY0 + row * (BH + BG)
    ok = "OK" if ry >= MIN_FEET_Y else "BLOCKED by ceiling!"
    print(f"  row {row}: top={ry}  {ok}")
print(f"  floor: {MAX_FEET_Y}")
print("----------------------")

# ---------- particles ----------
_particles = []

def spawn_particles(x, y, color, count=10):
    for _ in range(count):
        _particles.append({
            "x":    float(x),
            "y":    float(y),
            "vx":   random.uniform(-3.0, 3.0),
            "vy":   random.uniform(-5.0, -0.5),
            "life": random.randint(30, 55),
            "max":  50,
            "r":    random.randint(3, 6),
            "col":  color,
        })

def update_particles():
    for p in _particles:
        p["x"]  += p["vx"]
        p["y"]  += p["vy"]
        p["vy"] += 0.15
        p["life"] -= 1
    _particles[:] = [p for p in _particles if p["life"] > 0]

def draw_particles(surf):
    for p in _particles:
        alpha = p["life"] / p["max"]
        c = tuple(min(255, int(ch * alpha)) for ch in p["col"])
        r = max(1, int(p["r"] * alpha))
        pygame.draw.circle(surf, c, (int(p["x"]), int(p["y"])), r)

# ---------- rising symbol animation ----------
_rising = []

def spawn_rising(x, y, text, color):
    _rising.append({
        "x":    float(x),
        "y":    float(y),
        "text": text,
        "col":  color,
        "vy":   -4.5,
        "life": 50,
        "max":  50,
    })

def update_rising():
    for r in _rising:
        r["y"]    += r["vy"]
        r["vy"]   *= 0.92
        r["life"] -= 1
    _rising[:] = [r for r in _rising if r["life"] > 0]

def draw_rising(surf):
    for r in _rising:
        alpha = r["life"] / r["max"]
        c = tuple(min(255, int(ch * alpha)) for ch in r["col"])
        s = FONT_MED.render(r["text"], True, c)
        surf.blit(s, (int(r["x"]) - s.get_width()//2,
                      int(r["y"]) - s.get_height()//2))

# ---------- stick figure ----------
class Figure:
    SPEED  = 4.2
    GRAV   = 0.6
    JUMP_V = -12.5

    def __init__(self):
        # Start on the "7" button (index 4 in buttons list)
        b = buttons[4]
        self.x = float(b["rect"].centerx)
        self.y = float(b["rect"].top)      # y = feet level
        self.vx       = 0.0
        self.vy       = 0.0
        self.grounded = True
        self.j_held   = False
        self.walk_t   = 0.0
        self.facing   = 1
        self.anim_press    = 0   # countdown for press animation
        self.anim_celebrate= 0
        self.anim_blink    = 0
        self.standing_on   = None   # button dict or None

    def handle_keys(self, keys):
        # Horizontal
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.SPEED
            self.facing = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.SPEED
            self.facing = 1
        else:
            self.vx *= 0.5

        # Jump — press once
        want_jump = keys[pygame.K_UP] or keys[pygame.K_w]
        if want_jump and not self.j_held and self.grounded:
            self.vy = self.JUMP_V
            self.grounded = False
            spawn_particles(int(self.x), int(self.y), COL_CYAN, count=6)
        self.j_held = bool(want_jump)

        if abs(self.vx) > 0.3:
            self.walk_t += 0.22

    def update(self):
        # --- horizontal ---
        self.x += self.vx
        self.x = max(float(CX + FIG_HALF + 4),
                     min(float(CX + CW - FIG_HALF - 4), self.x))

        # --- vertical ---
        self.vy += self.GRAV
        self.y  += self.vy

        # Platform collision (only when falling)
        self.grounded = False
        if self.vy >= 0:
            for btn in buttons:
                r = btn["rect"]
                # Must be horizontally over the button
                if r.left + 5 < self.x < r.right - 5:
                    surface = float(r.top)
                    # Feet crossed the surface this frame
                    prev_y = self.y - self.vy
                    if prev_y <= surface and self.y >= surface:
                        self.y = surface
                        self.vy = 0.0
                        self.grounded = True
                        break

            # Calc floor fallback
            if not self.grounded and self.y >= MAX_FEET_Y:
                self.y = float(MAX_FEET_Y)
                self.vy = 0.0
                self.grounded = True

        # Hard ceiling — feet cannot go above MIN_FEET_Y
        if self.y < MIN_FEET_Y:
            self.y  = float(MIN_FEET_Y)
            self.vy = max(0.0, self.vy)

        # --- detect which button figure stands on ---
        self.standing_on = None
        if self.grounded:
            for btn in buttons:
                r = btn["rect"]
                if r.left + 5 < self.x < r.right - 5:
                    if abs(self.y - float(r.top)) <= 3:
                        self.standing_on = btn
                        break

        # --- timers ---
        if self.anim_press     > 0: self.anim_press     -= 1
        if self.anim_celebrate > 0: self.anim_celebrate -= 1
        if self.anim_blink     > 0: self.anim_blink     -= 1
        if random.random() < 0.004: self.anim_blink = 9

    def press(self):
        """
        Called when SPACE is pressed.
        Returns the button key string, or None if not on a button.
        """
        btn = self.standing_on
        if btn is None:
            return None

        # Trigger animations
        self.anim_press     = 20
        self.anim_celebrate = 40
        btn["flash"] = 22

        # Particles — plain circles only, no text (avoids font issues)
        col = btn_label_color(btn["key"])
        spawn_particles(btn["rect"].centerx, btn["rect"].top - 4,
                        col, count=14)

        # Rising symbol
        spawn_rising(btn["rect"].centerx,
                     btn["rect"].top - 10,
                     btn["text"],
                     col)

        return btn["key"]

    def draw(self, surf):
        x  = int(self.x)
        fy = int(self.y)       # feet
        hy = fy - 36           # head centre

        pressing  = self.anim_press     > 0
        celebrate = self.anim_celebrate > 0

        # shadow
        pygame.draw.ellipse(surf, (25, 25, 44), (x-13, fy+1, 26, 6))

        # head
        pygame.draw.circle(surf, COL_WHITE, (x, hy), 11, 2)

        # eyes
        if self.anim_blink > 0:
            pygame.draw.line(surf, COL_WHITE, (x-4, hy-2), (x-1, hy-2), 2)
            pygame.draw.line(surf, COL_WHITE, (x+1, hy-2), (x+4, hy-2), 2)
        else:
            pygame.draw.circle(surf, COL_WHITE, (x-4, hy-2), 2)
            pygame.draw.circle(surf, COL_WHITE, (x+4, hy-2), 2)

        # mouth
        if celebrate:
            pygame.draw.arc(surf, COL_YELLOW,
                            pygame.Rect(x-5, hy+4, 10, 7),
                            math.pi, 2*math.pi, 2)
        else:
            pygame.draw.line(surf, COL_WHITE, (x-4, hy+5), (x+4, hy+5), 2)

        # body
        pygame.draw.line(surf, COL_WHITE, (x, hy+11), (x, fy-10), 2)

        # legs
        sw = int(10 * math.sin(self.walk_t)) if abs(self.vx) > 0.2 else 0
        pygame.draw.line(surf, COL_WHITE, (x, fy-10), (x-sw, fy), 2)
        pygame.draw.line(surf, COL_WHITE, (x, fy-10), (x+sw, fy), 2)

        # arms
        if pressing:
            # one arm pushes down onto button
            pygame.draw.line(surf, COL_WHITE,
                             (x, hy+13), (x + 16*self.facing, fy-14), 2)
            pygame.draw.circle(surf, COL_YELLOW,
                               (x + 16*self.facing, fy-14), 4)
            pygame.draw.line(surf, COL_WHITE,
                             (x, hy+13), (x - 10*self.facing, hy+20), 2)
        elif celebrate:
            t2 = self.walk_t * 4
            pygame.draw.line(surf, COL_WHITE,
                             (x, hy+13), (x-17, hy + int(5*math.sin(t2))), 2)
            pygame.draw.line(surf, COL_WHITE,
                             (x, hy+13), (x+17, hy + int(5*math.sin(t2+1))), 2)
        else:
            sw2 = int(8*math.sin(self.walk_t+math.pi)) if abs(self.vx)>0.2 else 0
            pygame.draw.line(surf, COL_WHITE,
                             (x, hy+13), (x-14, fy-20+sw2), 2)
            pygame.draw.line(surf, COL_WHITE,
                             (x, hy+13), (x+14, fy-20-sw2), 2)

        # glow active button + tooltip
        if self.standing_on:
            r   = self.standing_on["rect"]
            col = btn_label_color(self.standing_on["key"])
            pygame.draw.rect(surf, col, r, 3, border_radius=8)
            tip = FONT_XS.render("SPACE = press!", True, col)
            surf.blit(tip, (x - tip.get_width()//2, hy - 22))

# ---------- calculator display logic ----------
expr   = ""
result = ""
d_flash = 0

def apply_key(key):
    """Update the expression/result based on which button was pressed."""
    global expr, result, d_flash

    if key == "C":
        expr   = ""
        result = ""

    elif key == "del":
        if result:
            result = ""
        else:
            expr = expr[:-1]

    elif key == "=":
        # Only evaluate if there's something to evaluate
        if expr == "":
            return
        try:
            # Build a safe expression — only our own characters
            safe = expr.replace("%", "/100")
            ans  = eval(safe)   # expr only ever contains digits + - * / . %
            if isinstance(ans, float):
                # Clean up float display
                ans_str = f"{ans:.8f}".rstrip("0").rstrip(".")
            else:
                ans_str = str(ans)
            result = ans_str
        except ZeroDivisionError:
            result = "DIV/0"
        except Exception:
            result = "ERR"

    elif key == "sg":   # sign toggle
        if result:
            if result.startswith("-"): result = result[1:]
            else:                      result = "-" + result
        elif expr:
            if expr.startswith("-"): expr = expr[1:]
            else:                    expr = "-" + expr

    else:
        # Regular key: digit, operator, dot
        if result:
            if key in "0123456789.":
                # Start fresh number
                expr   = result
                result = ""
                expr   = key   # replace, not append
            else:
                # Chain: use result as left operand
                expr   = result + key
                result = ""
        else:
            expr += key
        d_flash = 22

# ---------- drawing ----------
def draw_background(surf):
    surf.fill(COL_BG)
    for gx in range(0, W, 32):
        pygame.draw.line(surf, (20, 20, 34), (gx, 0), (gx, H))
    for gy in range(0, H, 32):
        pygame.draw.line(surf, (20, 20, 34), (0, gy), (W, gy))

def draw_calc_body(surf):
    pygame.draw.rect(surf, COL_CALC,   (CX, CY, CW, CH), border_radius=18)
    pygame.draw.rect(surf, COL_BORDER, (CX, CY, CW, CH), 3, border_radius=18)
    brand = FONT_XS.render("DIGIT KEEPER  v3", True, COL_GRAY)
    surf.blit(brand, (CX + CW//2 - brand.get_width()//2, CY + 10))

def draw_display(surf):
    pygame.draw.rect(surf, COL_DISP,  (DX, DY, DW, DH), border_radius=8)
    pygame.draw.rect(surf, COL_DBRDR, (DX, DY, DW, DH), 2, border_radius=8)

    # Pretty-print: replace raw operators with nicer symbols for display
    def prettify(s):
        return (s.replace("*", "x")
                 .replace("/", "÷"))

    if result:
        # Show expression small on top, result big on bottom
        small = FONT_XS.render(prettify(expr), True, COL_GRAY)
        surf.blit(small, (DX + DW - small.get_width() - 8, DY + 4))
        big = FONT_BIG.render(result, True, COL_GREEN)
        surf.blit(big, (DX + DW - big.get_width() - 8,
                        DY + DH - big.get_height() - 4))
    else:
        col  = (90, 240, 130) if d_flash > 0 else (50, 150, 70)
        text = prettify(expr) if expr else "0"
        s    = FONT_BIG.render(text, True, col)
        # If too wide, anchor left
        draw_x = max(DX + 4, DX + DW - s.get_width() - 8)
        surf.blit(s, (draw_x, DY + DH - s.get_height() - 4))

def draw_buttons(surf):
    for btn in buttons:
        r     = btn["rect"]
        fl    = btn["flash"]
        bg    = btn["bg"]

        # Flash effect
        if fl > 0:
            t  = fl / 22.0
            bg = tuple(min(255, int(c + (255-c)*t*0.65)) for c in bg)
            btn["flash"] -= 1

        pygame.draw.rect(surf, bg, r, border_radius=7)
        pygame.draw.rect(surf, COL_BORDER, r, 1, border_radius=7)

        lc = btn_label_color(btn["key"])
        ls = FONT_SM.render(btn["text"], True, lc)
        surf.blit(ls, (r.centerx - ls.get_width()//2,
                       r.centery - ls.get_height()//2))

def draw_panel(surf, fig):
    px = CX + CW + 26
    py = CY

    # Title
    surf.blit(FONT_MED.render("DIGIT KEEPER 3", True, COL_CYAN), (px, py))
    py += 34
    surf.blit(FONT_XS.render("Walk to a button then press SPACE!", True, COL_GRAY),
              (px, py))
    py += 44

    # Standing on
    pygame.draw.rect(surf, COL_DARK,   (px, py, 320, 66), border_radius=10)
    pygame.draw.rect(surf, COL_BORDER, (px, py, 320, 66), 2, border_radius=10)
    surf.blit(FONT_XS.render("STANDING ON:", True, COL_GRAY), (px+10, py+6))
    if fig.standing_on:
        text = fig.standing_on["text"]
        col  = btn_label_color(fig.standing_on["key"])
        s    = FONT_BIG.render(text, True, col)
        surf.blit(s, (px + 160 - s.get_width()//2,
                      py + 33  - s.get_height()//2))
    else:
        surf.blit(FONT_XS.render("(between buttons)", True, (55, 55, 80)),
                  (px+10, py+28))
    py += 80

    # Expression
    pygame.draw.rect(surf, COL_DARK,   (px, py, 320, 44), border_radius=7)
    pygame.draw.rect(surf, COL_BORDER, (px, py, 320, 44), 1, border_radius=7)
    surf.blit(FONT_XS.render("EXPR:", True, COL_GRAY), (px+8, py+6))
    surf.blit(FONT_SM.render(expr if expr else "—", True, COL_GREEN), (px+8, py+22))
    py += 56

    # Result
    if result:
        pygame.draw.rect(surf, COL_DARK,   (px, py, 320, 44), border_radius=7)
        pygame.draw.rect(surf, COL_BORDER, (px, py, 320, 44), 1, border_radius=7)
        surf.blit(FONT_XS.render("RESULT:", True, COL_GRAY), (px+8, py+6))
        surf.blit(FONT_SM.render(result, True, COL_LIME), (px+8, py+22))
        py += 56

    # Controls
    py += 8
    surf.blit(FONT_SM.render("CONTROLS", True, COL_CYAN), (px, py))
    py += 26
    for key_name, desc in [
        ("A / D   or   ← →", "Walk"),
        ("W       or   ↑",   "Jump"),
        ("SPACE",             "Press button"),
        ("ESC",               "Quit"),
    ]:
        surf.blit(FONT_XS.render(key_name,      True, COL_YELLOW), (px,     py))
        surf.blit(FONT_XS.render("— " + desc,   True, COL_WHITE),  (px+160, py))
        py += 20

    # Tip
    py += 12
    tips = [
        "Jump up to reach higher button rows!",
        "Walk to  =  and press SPACE to evaluate.",
        "Try building:  9 + 3  then press  =",
        "C clears everything.",
    ]
    tip = tips[(pygame.time.get_ticks() // 3000) % len(tips)]
    surf.blit(FONT_XS.render("Tip: " + tip, True, (90, 150, 110)), (px, py))

# ---------- main loop ----------
figure    = Figure()
space_held = False

running = True
while running:
    clock.tick(60)

    # events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE and not space_held:
                space_held = True
                key = figure.press()
                if key is not None:
                    apply_key(key)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                space_held = False

    # update
    keys = pygame.key.get_pressed()
    figure.handle_keys(keys)
    figure.update()

    if d_flash > 0:
        d_flash -= 1

    update_particles()
    update_rising()

    # draw
    draw_background(screen)
    draw_calc_body(screen)
    draw_buttons(screen)
    draw_display(screen)
    draw_rising(screen)
    draw_particles(screen)
    figure.draw(screen)
    draw_panel(screen, figure)

    pygame.display.flip()

pygame.quit()
sys.exit()
