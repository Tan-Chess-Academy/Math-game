"""
╔══════════════════════════════════════════════════════════╗
║           DIGIT KEEPER — Calculator World                ║
║   A stick figure lives inside a calculator!              ║
║                                                          ║
║  Run:  python digit_keeper.py                            ║
╚══════════════════════════════════════════════════════════╝

CONTROLS:
  1-9        — Stick figure picks up that digit
  0          — Pick up 0
  WASD / Arrows — Move around
  SPACE      — Toss the digit
  C          — Clear / drop digit
  ESC        — Quit
"""

import pygame
import math
import random
import sys

pygame.init()

W, H = 900, 680
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DIGIT KEEPER — Calculator World")
clock = pygame.time.Clock()
FPS  = 60

# ── Fonts ──────────────────────────────────────────────────
def font(size, bold=False):
    for name in ["Consolas", "Courier New", None]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except:
            pass
    return pygame.font.Font(None, size)

F_GIANT  = font(120, bold=True)
F_BIG    = font(64,  bold=True)
F_MED    = font(36,  bold=True)
F_SM     = font(22)
F_XS     = font(16)
F_TINY   = font(13)

# ── Colors ─────────────────────────────────────────────────
BG          = (18,  18,  28)
CALC_BODY   = (28,  28,  42)
CALC_BORDER = (60,  60,  90)
SCREEN_BG   = (10,  20,  15)
SCREEN_GLOW = (30,  90,  50)
BTN_DARK    = (35,  35,  55)
BTN_LIT     = (50,  50,  80)
BTN_NUM     = (45,  45,  70)
BTN_OP      = (60,  40,  80)
BTN_EQ      = (30,  90,  60)
BTN_CLR     = (90,  30,  40)
WHITE       = (240, 245, 255)
GREEN       = (80,  255, 140)
CYAN        = (0,   220, 255)
YELLOW      = (255, 230,  60)
ORANGE      = (255, 150,  40)
RED         = (255,  70,  70)
GRAY        = (120, 120, 150)
DARK        = (20,  20,  35)
PURPLE      = (160,  80, 255)

# ── Calculator layout ──────────────────────────────────────
CALC_X = 50
CALC_Y = 40
CALC_W = 380
CALC_H = 580

SCREEN_X = CALC_X + 20
SCREEN_Y = CALC_Y + 20
SCREEN_W = CALC_W - 40
SCREEN_H = 100

# Button grid
BTN_START_X = CALC_X + 20
BTN_START_Y = CALC_Y + 140
BTN_W = 74
BTN_H = 54
BTN_GAP = 8

# Layout: label, col, row, color, is_op
BUTTONS = [
    ("C",  0, 0, BTN_CLR, True),  ("±", 1, 0, BTN_OP, True),
    ("%",  2, 0, BTN_OP,  True),  ("÷", 3, 0, BTN_OP, True),
    ("7",  0, 1, BTN_NUM, False), ("8", 1, 1, BTN_NUM, False),
    ("9",  2, 1, BTN_NUM, False), ("×", 3, 1, BTN_OP, True),
    ("4",  0, 2, BTN_NUM, False), ("5", 1, 2, BTN_NUM, False),
    ("6",  2, 2, BTN_NUM, False), ("−", 3, 2, BTN_OP, True),
    ("1",  0, 3, BTN_NUM, False), ("2", 1, 3, BTN_NUM, False),
    ("3",  2, 3, BTN_NUM, False), ("+", 3, 3, BTN_OP, True),
    ("0",  0, 4, BTN_NUM, False), (".", 1, 4, BTN_NUM, False),
    ("=",  2, 4, BTN_EQ,  True),  ("⌫", 3, 4, BTN_CLR, True),
]

def btn_rect(col, row):
    x = BTN_START_X + col * (BTN_W + BTN_GAP)
    y = BTN_START_Y + row * (BTN_H + BTN_GAP)
    return pygame.Rect(x, y, BTN_W, BTN_H)

# ── Particles ──────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, text=None, vx=None, vy=None, life=50, size=5):
        self.x, self.y = float(x), float(y)
        self.color = color
        self.text  = text
        self.vx = vx if vx is not None else random.uniform(-2.5, 2.5)
        self.vy = vy if vy is not None else random.uniform(-4,  -0.5)
        self.life = self.maxlife = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surf):
        a = self.life / self.maxlife
        c = tuple(int(ch * a) for ch in self.color)
        if self.text:
            s = F_SM.render(self.text, True, c)
            surf.blit(s, (int(self.x), int(self.y)))
        else:
            r = max(1, int(self.size * a))
            pygame.draw.circle(surf, c, (int(self.x), int(self.y)), r)

particles = []

def burst(x, y, color, n=14, texts=None):
    for _ in range(n):
        t = random.choice(texts) if texts else None
        particles.append(Particle(x, y, color, text=t))

# ── Tossed Digit ───────────────────────────────────────────
class TossedDigit:
    def __init__(self, x, y, digit, vx, vy):
        self.x, self.y = float(x), float(y)
        self.digit = digit
        self.vx, self.vy = vx, vy
        self.angle = 0
        self.spin  = random.uniform(-8, 8)
        self.alive = True
        self.age   = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.4
        self.angle += self.spin
        self.age   += 1
        if self.age > 80:
            self.alive = False
        # bounce off calc walls loosely
        if self.x < CALC_X+10 or self.x > CALC_X+CALC_W-10:
            self.vx *= -0.6
        if self.y > CALC_Y+CALC_H-10:
            self.vy *= -0.5
            self.y   = CALC_Y+CALC_H-10

    def draw(self, surf):
        a = max(0, 1 - self.age/80)
        col = tuple(int(ch*a) for ch in YELLOW)
        s = F_BIG.render(self.digit, True, col)
        rot = pygame.transform.rotate(s, self.angle)
        r = rot.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rot, r)

tossed = []

# ── Stick Figure ───────────────────────────────────────────
class StickFigure:
    SPEED = 3.5

    def __init__(self):
        # Start inside the calculator screen area
        self.x   = float(CALC_X + CALC_W//2)
        self.y   = float(CALC_Y + CALC_H - 80)
        self.vx  = 0.0
        self.vy  = 0.0
        self.on_ground = False
        self.walk_t    = 0.0
        self.held_digit = None   # e.g. "7"
        self.digit_scale= 1.0    # bounce scale when picked up
        self.facing     = 1      # 1=right -1=left
        self.jump_pressed = False
        self.celebrating = 0     # frames of celebration anim
        self.blinking    = 0     # eye blink timer

        # Allowed region (inside calculator body)
        self.min_x = CALC_X + 18
        self.max_x = CALC_X + CALC_W - 18
        self.min_y = CALC_Y + SCREEN_Y + SCREEN_H + 10  # below display screen
        self.max_y = CALC_Y + CALC_H - 30

    # ── ground detection: buttons act as platforms ──────────
    def ground_y_at(self, x, y):
        """Return the y of the surface the figure stands on."""
        # Check button tops
        for label, col, row, color, is_op in BUTTONS:
            r = btn_rect(col, row)
            if r.left - 5 < x < r.right + 5:
                top = r.top
                if y <= top + 4:
                    return top
        # Calculator floor
        return self.max_y

    def handle_input(self, keys):
        moving = False
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.vx = -self.SPEED; self.facing = -1; moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx =  self.SPEED; self.facing =  1; moving = True
        else:
            self.vx *= 0.7

        # Jump
        if (keys[pygame.K_UP] or keys[pygame.K_w]):
            if self.on_ground and not self.jump_pressed:
                self.vy = -10
                self.on_ground = False
                self.jump_pressed = True
                burst(int(self.x), int(self.y)+20, CYAN, n=8)
        else:
            self.jump_pressed = False

        if moving:
            self.walk_t += 0.2

    def update(self):
        self.x += self.vx
        self.vy += 0.5   # gravity
        self.y  += self.vy

        # Clamp x
        self.x = max(self.min_x, min(self.max_x, self.x))

        # Ground / platform collision
        gy = self.ground_y_at(self.x, self.y + 34)
        if self.y + 34 >= gy:
            self.y = gy - 34
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # Ceiling
        ceil_y = SCREEN_Y + SCREEN_H + 20
        if self.y - 40 < ceil_y:
            self.y = ceil_y + 40
            self.vy = abs(self.vy) * 0.3

        # Digit scale bounce
        if self.digit_scale > 1.0:
            self.digit_scale -= 0.05
            self.digit_scale  = max(1.0, self.digit_scale)

        # Celebration
        if self.celebrating > 0:
            self.celebrating -= 1

        # Blink timer
        self.blinking = max(0, self.blinking - 1)
        if random.random() < 0.005:
            self.blinking = 8

    def pick_digit(self, d):
        self.held_digit  = d
        self.digit_scale = 1.6
        self.celebrating = 40
        burst(int(self.x), int(self.y)-50, YELLOW, n=16,
              texts=[d, d, "!"])

    def toss_digit(self):
        if self.held_digit is None:
            return
        vx = 7 * self.facing
        vy = -8
        tossed.append(TossedDigit(self.x + 20*self.facing,
                                  self.y - 20, self.held_digit, vx, vy))
        burst(int(self.x), int(self.y)-20, ORANGE, n=10)
        self.held_digit = None

    def draw(self, surf):
        x, y = int(self.x), int(self.y)

        # shadow
        pygame.draw.ellipse(surf, (30,30,50),
                            (x-16, y+32, 32, 8))

        col = WHITE
        celebrate = self.celebrating > 0

        # -- HEAD --
        pygame.draw.circle(surf, col, (x, y-28), 12, 2)
        # eyes
        eye_y = y - 30
        if self.blinking > 0:
            pygame.draw.line(surf, col, (x-5, eye_y), (x-2, eye_y), 2)
            pygame.draw.line(surf, col, (x+2, eye_y), (x+5, eye_y), 2)
        else:
            pygame.draw.circle(surf, col, (x-4, eye_y), 2)
            pygame.draw.circle(surf, col, (x+4, eye_y), 2)
        # smile / excited mouth
        if celebrate:
            pygame.draw.arc(surf, YELLOW,
                            (x-6, y-22, 12, 8), math.pi, 2*math.pi, 2)
        else:
            pygame.draw.line(surf, col, (x-4, y-20), (x+4, y-20), 2)

        # -- BODY --
        pygame.draw.line(surf, col, (x, y-16), (x, y+10), 2)

        # -- LEGS --
        lsway = int(10 * math.sin(self.walk_t)) if self.vx != 0 else 0
        pygame.draw.line(surf, col, (x, y+10), (x - lsway, y+34), 2)
        pygame.draw.line(surf, col, (x, y+10), (x + lsway, y+34), 2)

        # -- ARMS --
        if self.held_digit:
            # Both arms raised holding digit above head
            arm_raise = -10 if not celebrate else -18 + int(4*math.sin(self.walk_t*3))
            pygame.draw.line(surf, col, (x, y-6),
                             (x - 18, y + arm_raise), 2)
            pygame.draw.line(surf, col, (x, y-6),
                             (x + 18, y + arm_raise), 2)

            # Held digit — above head, scaled
            digit_surf = F_BIG.render(self.held_digit, True, YELLOW)
            sc = self.digit_scale
            if sc != 1.0:
                nw = int(digit_surf.get_width()  * sc)
                nh = int(digit_surf.get_height() * sc)
                digit_surf = pygame.transform.scale(digit_surf, (nw, nh))

            # glow behind digit
            gw, gh = digit_surf.get_width(), digit_surf.get_height()
            glow_surf = pygame.Surface((gw+20, gh+20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (255,230,60,60),
                                (0, 0, gw+20, gh+20))
            surf.blit(glow_surf, (x - (gw+20)//2, y - 80 - (gh+20)//2))
            surf.blit(digit_surf, (x - gw//2, y - 80 - gh//2))

            # sparkles around digit
            if celebrate:
                for i in range(4):
                    ang = self.walk_t * 3 + i * math.pi/2
                    sx2 = x + int(28*math.cos(ang))
                    sy2 = y - 80 + int(12*math.sin(ang))
                    pygame.draw.circle(surf, YELLOW, (sx2, sy2), 3)

        else:
            # Normal idle / walking arms
            asway = int(8*math.sin(self.walk_t + math.pi)) if self.vx != 0 else 0
            pygame.draw.line(surf, col, (x, y-6), (x-14, y+4+asway), 2)
            pygame.draw.line(surf, col, (x, y-6), (x+14, y+4-asway), 2)

    def rect(self):
        return pygame.Rect(self.x-14, self.y-40, 28, 72)


# ── Calculator display expression ─────────────────────────
display_expr   = ""
display_result = ""
display_flash  = 0   # frames to flash green on new digit

# ── Draw calculator body ───────────────────────────────────
def draw_calculator(surf, active_btn=None):
    # Body
    pygame.draw.rect(surf, CALC_BODY,
                     (CALC_X, CALC_Y, CALC_W, CALC_H), border_radius=20)
    pygame.draw.rect(surf, CALC_BORDER,
                     (CALC_X, CALC_Y, CALC_W, CALC_H), 3, border_radius=20)

    # Brand label
    brand = F_XS.render("DIGIT KEEPER  v1.0", True, GRAY)
    surf.blit(brand, (CALC_X + CALC_W//2 - brand.get_width()//2,
                      CALC_Y + 6))

    # Screen
    pygame.draw.rect(surf, SCREEN_BG,
                     (SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H),
                     border_radius=8)
    pygame.draw.rect(surf, SCREEN_GLOW,
                     (SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H),
                     2, border_radius=8)

    # Display text
    if display_result:
        res_s = F_BIG.render(display_result, True, GREEN)
        surf.blit(res_s, (SCREEN_X + SCREEN_W - res_s.get_width() - 8,
                          SCREEN_Y + SCREEN_H - res_s.get_height() - 4))
        expr_s = F_XS.render(display_expr, True, GRAY)
        surf.blit(expr_s, (SCREEN_X + 6, SCREEN_Y + 6))
    else:
        col = GREEN if display_flash > 0 else (100, 200, 120)
        expr_s = F_MED.render(display_expr if display_expr else "0", True, col)
        surf.blit(expr_s, (SCREEN_X + SCREEN_W - expr_s.get_width() - 8,
                           SCREEN_Y + SCREEN_H - expr_s.get_height() - 4))

    # Buttons
    for label, col, row, color, is_op in BUTTONS:
        r = btn_rect(col, row)
        lit = (active_btn == label)
        c = tuple(min(255, ch + 30) for ch in color) if lit else color
        pygame.draw.rect(surf, c, r, border_radius=6)
        pygame.draw.rect(surf, CALC_BORDER, r, 1, border_radius=6)

        # Label
        lcol = WHITE if not is_op else (
            YELLOW if label in ("=",) else
            (RED if label in ("C","⌫") else CYAN))
        ls = F_SM.render(label, True, lcol)
        surf.blit(ls, (r.centerx - ls.get_width()//2,
                       r.centery - ls.get_height()//2))

        # Tiny key hint for digits
        if label.isdigit():
            hs = F_TINY.render(f"[{label}]", True, (80,80,110))
            surf.blit(hs, (r.x+3, r.y+3))


# ── Right panel — instructions & info ─────────────────────
def draw_panel(surf, figure):
    px = CALC_X + CALC_W + 30
    py = CALC_Y

    # Title
    t = F_MED.render("DIGIT KEEPER", True, CYAN)
    surf.blit(t, (px, py))

    sub = F_XS.render("A stick figure in a calculator", True, GRAY)
    surf.blit(sub, (px, py+38))

    # Current held digit display
    py2 = py + 80
    pygame.draw.rect(surf, DARK, (px, py2, 360, 100), border_radius=10)
    pygame.draw.rect(surf, CALC_BORDER, (px, py2, 360, 100), 2, border_radius=10)

    hl = F_XS.render("HOLDING:", True, GRAY)
    surf.blit(hl, (px+12, py2+10))

    if figure.held_digit:
        hd = F_GIANT.render(figure.held_digit, True, YELLOW)
        surf.blit(hd, (px + 180 - hd.get_width()//2,
                       py2 + 50  - hd.get_height()//2))
    else:
        nd = F_MED.render("nothing", True, (60,60,90))
        surf.blit(nd, (px + 180 - nd.get_width()//2, py2+36))

    # Controls
    py3 = py2 + 120
    controls = [
        ("KEYS 0–9",   "Pick up a digit"),
        ("← → / A D",  "Walk left / right"),
        ("↑ / W",       "Jump"),
        ("SPACE",       "Toss the digit"),
        ("C",           "Drop / clear digit"),
        ("ESC",         "Quit"),
    ]
    cl = F_SM.render("CONTROLS", True, CYAN)
    surf.blit(cl, (px, py3))
    py3 += 30

    for key, desc in controls:
        ks = F_XS.render(key, True, YELLOW)
        ds = F_XS.render("— " + desc, True, WHITE)
        surf.blit(ks,  (px,      py3))
        surf.blit(ds,  (px+120,  py3))
        py3 += 22

    # Tips
    py3 += 14
    tips = [
        "💡 Jump on the buttons!",
        "💡 The digit floats above your head.",
        "💡 Toss digits to see them fly!",
        "💡 Each key lights up its button.",
    ]
    tip = tips[(pygame.time.get_ticks()//3000) % len(tips)]
    ts = F_XS.render(tip, True, (100,160,120))
    surf.blit(ts, (px, py3))

    # Expression history
    py3 += 36
    eh = F_XS.render("EXPRESSION:", True, GRAY)
    surf.blit(eh, (px, py3))
    py3 += 20
    pygame.draw.rect(surf, DARK, (px, py3, 360, 32), border_radius=6)
    ex = F_SM.render(display_expr if display_expr else "—", True, GREEN)
    surf.blit(ex, (px+8, py3+6))


# ── Background grid (graph paper feel) ────────────────────
def draw_bg(surf):
    surf.fill(BG)
    for gx in range(0, W, 30):
        pygame.draw.line(surf, (25,25,40), (gx,0),(gx,H))
    for gy in range(0, H, 30):
        pygame.draw.line(surf, (25,25,40), (0,gy),(W,gy))


# ── MAIN ──────────────────────────────────────────────────
figure     = StickFigure()
active_btn = None
btn_flash  = 0

running = True
while running:
    clock.tick(FPS)

    # ── Events ────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # Digit keys 0–9
            elif event.unicode in "0123456789":
                d = event.unicode
                figure.pick_digit(d)
                display_expr += d
                display_result = ""
                display_flash  = 20
                active_btn = d
                btn_flash  = 18

            # Toss
            elif event.key == pygame.K_SPACE:
                figure.toss_digit()

            # Clear / drop
            elif event.key == pygame.K_c:
                figure.held_digit = None
                display_expr  = ""
                display_result = ""
                active_btn = "C"
                btn_flash  = 18
                burst(int(figure.x), int(figure.y)-20, RED, n=10)

            # Operators (just for display expression building)
            elif event.unicode in "+-*/":
                sym = {"+" : "+", "-" : "−", "*" : "×", "/" : "÷"}[event.unicode]
                display_expr  += sym
                display_result = ""
                active_btn = sym
                btn_flash  = 18

            # Evaluate on Enter
            elif event.key == pygame.K_RETURN:
                try:
                    safe = display_expr.replace("÷","/").replace("×","*").replace("−","-")
                    result = eval(safe)
                    display_result = str(result)
                    active_btn = "="
                    btn_flash  = 18
                    burst(int(figure.x), int(figure.y)-40, GREEN, n=20,
                          texts=["=", str(result)])
                except:
                    display_result = "ERR"

            # Backspace
            elif event.key == pygame.K_BACKSPACE:
                display_expr   = display_expr[:-1]
                display_result = ""
                active_btn = "⌫"
                btn_flash  = 18

    # ── Update ────────────────────────────────────────────
    keys = pygame.key.get_pressed()
    figure.handle_input(keys)
    figure.update()

    if btn_flash > 0:
        btn_flash -= 1
    else:
        active_btn = None

    if display_flash > 0:
        display_flash -= 1

    for td in tossed:
        td.update()
    tossed[:] = [td for td in tossed if td.alive]

    for pt in particles:
        pt.update()
    particles[:] = [pt for pt in particles if pt.life > 0]

    # ── Draw ──────────────────────────────────────────────
    draw_bg(screen)
    draw_calculator(screen, active_btn)

    # Draw tossed digits (inside calc space)
    for td in tossed:
        td.draw(screen)

    # Draw particles
    for pt in particles:
        pt.draw(screen)

    # Draw stick figure
    figure.draw(screen)

    # Right panel
    draw_panel(screen, figure)

    pygame.display.flip()

pygame.quit()
sys.exit()
