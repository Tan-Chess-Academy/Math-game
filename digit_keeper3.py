"""
╔══════════════════════════════════════════════════════════╗
║         DIGIT KEEPER 3 — The Figure Does the Math        ║
║                                                          ║
║  The stick figure WALKS to buttons and PRESSES them!     ║
║  Run:  python3 digit_keeper3.py                          ║
╚══════════════════════════════════════════════════════════╝

CONTROLS:
  WASD / Arrow Keys  — Walk the stick figure
  SPACE              — Press the button you're standing on
  ESC                — Quit

  The figure must physically walk to a button and press
  SPACE to add it to the calculator display!
"""

import pygame
import math
import random
import sys

pygame.init()

W, H = 1000, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DIGIT KEEPER 3 — The Figure Does the Math")
clock = pygame.time.Clock()
FPS   = 60

# ── Fonts ──────────────────────────────────────────────────
def fnt(size, bold=False):
    for name in ["Consolas", "Courier New", None]:
        try: return pygame.font.SysFont(name, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

F_GIANT = fnt(88,  bold=True)
F_BIG   = fnt(52,  bold=True)
F_MED   = fnt(32,  bold=True)
F_SM    = fnt(21,  bold=True)
F_XS    = fnt(15)
F_TINY  = fnt(12)

# ── Colors ─────────────────────────────────────────────────
BG          = (13, 13, 22)
CALC_BODY   = (26, 26, 40)
CALC_BORDER = (55, 55, 88)
DISP_BG     = (8,  20, 13)
DISP_BORDER = (38, 130, 65)
BTN_NUM     = (36, 36, 56)
BTN_OP      = (54, 34, 72)
BTN_EQ      = (24, 82, 52)
BTN_CLR     = (82, 26, 36)
WHITE       = (235, 240, 255)
GREEN       = (65,  250, 125)
CYAN        = (0,   205, 250)
YELLOW      = (255, 225,  45)
ORANGE      = (255, 145,  30)
RED         = (255,  60,  60)
PURPLE      = (170,  70, 250)
GRAY        = (105, 105, 140)
DARK        = (16,  16,  28)
PINK        = (255, 105, 175)
LIME        = (130, 255,  80)

# ── Calculator geometry ────────────────────────────────────
CALC_X, CALC_Y = 55,  30
CALC_W, CALC_H = 500, 650

DISP_X = CALC_X + 20
DISP_Y = CALC_Y + 36
DISP_W = CALC_W - 40
DISP_H = 95

BTN_AREA_Y = DISP_Y + DISP_H + 22
BTN_W, BTN_H, BTN_GAP = 96, 62, 9

BUTTONS = [
    ("C",  0,0,BTN_CLR,True), ("±",1,0,BTN_OP,True),
    ("%",  2,0,BTN_OP, True), ("÷",3,0,BTN_OP,True),
    ("7",  0,1,BTN_NUM,False),("8",1,1,BTN_NUM,False),
    ("9",  2,1,BTN_NUM,False),("×",3,1,BTN_OP,True),
    ("4",  0,2,BTN_NUM,False),("5",1,2,BTN_NUM,False),
    ("6",  2,2,BTN_NUM,False),("−",3,2,BTN_OP,True),
    ("1",  0,3,BTN_NUM,False),("2",1,3,BTN_NUM,False),
    ("3",  2,3,BTN_NUM,False),("+",3,3,BTN_OP,True),
    ("0",  0,4,BTN_NUM,False),(".",1,4,BTN_NUM,False),
    ("=",  2,4,BTN_EQ, True), ("⌫",3,4,BTN_CLR,True),
]

def btn_rect(col, row):
    x = CALC_X + 20 + col*(BTN_W + BTN_GAP)
    y = BTN_AREA_Y  + row*(BTN_H + BTN_GAP)
    return pygame.Rect(x, y, BTN_W, BTN_H)

# Pre-build button rects for collision
BTN_DATA = []   # (label, rect, color, is_op)
for label, col, row, color, is_op in BUTTONS:
    BTN_DATA.append((label, btn_rect(col, row), color, is_op))

SYM_COLORS = {
    "+": GREEN,  "−": CYAN,  "×": ORANGE, "÷": PURPLE,
    "%": PINK,   "±": YELLOW,"=": LIME,   "C": RED,
    "⌫": RED,   ".": WHITE,
}
for d in "0123456789": SYM_COLORS[d] = YELLOW

def sym_col(s): return SYM_COLORS.get(s, WHITE)

# ── Particles ──────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, col, text=None, vx=None, vy=None, life=55, size=5):
        self.x, self.y = float(x), float(y)
        self.col = col; self.text = text
        self.vx  = vx  if vx  is not None else random.uniform(-3, 3)
        self.vy  = vy  if vy  is not None else random.uniform(-4.5, -0.5)
        self.life = self.maxlife = life
        self.size = size
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.vy+=0.15; self.life-=1
    def draw(self, surf):
        a = self.life/self.maxlife
        c = tuple(int(ch*a) for ch in self.col)
        if self.text:
            s = F_SM.render(self.text, True, c)
            surf.blit(s, (int(self.x), int(self.y)))
        else:
            r = max(1, int(self.size*a))
            pygame.draw.circle(surf, c, (int(self.x), int(self.y)), r)

particles = []
def burst(x, y, col, n=12, texts=None):
    for _ in range(n):
        t = random.choice(texts) if texts else None
        particles.append(Particle(x, y, col, text=t))

# ── Press animation ────────────────────────────────────────
class BtnPressAnim:
    """Visual flash that plays when a button is pressed."""
    def __init__(self, rect, label, color):
        self.rect  = rect
        self.label = label
        self.color = color
        self.life  = 22
        self.maxlife = 22
    def update(self): self.life -= 1
    def alive(self): return self.life > 0
    def draw(self, surf):
        a = self.life / self.maxlife
        c = tuple(min(255, int(ch + (255-ch)*a*0.6)) for ch in self.color)
        pygame.draw.rect(surf, c, self.rect, border_radius=8)
        # ripple ring
        grow = int((1-a)*20)
        r2 = self.rect.inflate(grow, grow)
        pygame.draw.rect(surf, tuple(int(ch*a*0.8) for ch in self.color),
                         r2, 2, border_radius=10)

press_anims = []

# ── Floating digit rising from button to display ───────────
class RisingSymbol:
    def __init__(self, x, y, sym):
        self.x    = float(x)
        self.y    = float(y)
        self.sym  = sym
        self.col  = sym_col(sym)
        self.vy   = -5.5
        self.life = 60
        self.maxlife = 60
        self.scale = 1.0
    def update(self):
        self.y   += self.vy
        self.vy  *= 0.92
        self.life -= 1
        self.scale = 0.6 + 0.4*(self.life/self.maxlife)
    def alive(self): return self.life > 0
    def draw(self, surf):
        a = self.life/self.maxlife
        col = tuple(int(ch*a) for ch in self.col)
        s   = F_MED.render(self.sym, True, col)
        sc  = self.scale
        ns  = pygame.transform.scale(s,(int(s.get_width()*sc),int(s.get_height()*sc)))
        surf.blit(ns,(int(self.x)-ns.get_width()//2, int(self.y)-ns.get_height()//2))

rising_syms = []

# ── Stick Figure ───────────────────────────────────────────
class Figure:
    SPEED = 4.0

    def __init__(self):
        # Start at the top of the first button row
        first_btn = BTN_DATA[4][1]  # "7" button
        self.x = float(first_btn.centerx)
        self.y = float(first_btn.top - 2)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground  = True
        self.walk_t     = 0.0
        self.facing     = 1
        self.jump_lock  = False
        self.pressing   = 0    # animation frames for pressing action
        self.celebrate  = 0
        self.blink      = 0
        self.current_btn = None   # which button figure is on

    def get_platform_y(self, x):
        """Return the top-y of any button the figure is standing over, else floor."""
        for label, rect, color, is_op in BTN_DATA:
            if rect.left - 8 < x < rect.right + 8:
                return rect.top
        return CALC_Y + CALC_H - 18   # calc floor

    def handle_input(self, keys):
        moved = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.SPEED; self.facing = -1; moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.SPEED;  self.facing =  1; moved = True
        else:
            self.vx *= 0.6

        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground and not self.jump_lock:
            self.vy = -11
            self.on_ground = False
            self.jump_lock = True
            burst(int(self.x), int(self.y)+4, CYAN, n=8)
        if not (keys[pygame.K_UP] or keys[pygame.K_w]):
            self.jump_lock = False

        if moved: self.walk_t += 0.22

    def update(self):
        self.x += self.vx
        self.vy += 0.55
        self.y  += self.vy

        # Clamp x inside calculator
        self.x = max(CALC_X + 18, min(CALC_X + CALC_W - 18, self.x))

        # Platform / ground landing
        gy = self.get_platform_y(self.x)
        if self.y >= gy - 2:
            self.y = float(gy)
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # Ceiling
        ceil = DISP_Y + DISP_H + 10
        if self.y - 48 < ceil:
            self.y = float(ceil + 48)
            self.vy = abs(self.vy)*0.3

        if self.pressing  > 0: self.pressing  -= 1
        if self.celebrate > 0: self.celebrate -= 1
        if self.blink     > 0: self.blink     -= 1
        if random.random() < 0.004: self.blink = 9

        # Detect which button figure stands on
        self.current_btn = None
        for label, rect, color, is_op in BTN_DATA:
            if rect.left - 6 < self.x < rect.right + 6 and abs(self.y - rect.top) < 5:
                self.current_btn = (label, rect, color)
                break

    def press_button(self):
        """Called when SPACE is pressed — triggers press anim & returns button label."""
        if self.current_btn is None:
            return None
        label, rect, color = self.current_btn
        self.pressing   = 18
        self.celebrate  = 35
        # Press animation
        press_anims.append(BtnPressAnim(rect, label, sym_col(label)))
        # Rising symbol
        rising_syms.append(RisingSymbol(rect.centerx, rect.top - 10, label))
        # Particles from button
        burst(rect.centerx, rect.top, sym_col(label), n=16,
              texts=[label, label])
        return label

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        pressing = self.pressing > 0
        cel      = self.celebrate > 0
        col      = WHITE

        # Shadow
        pygame.draw.ellipse(surf, (30,30,50), (x-15, y+2, 30, 8))

        # HEAD
        pygame.draw.circle(surf, col, (x, y-30), 12, 2)

        # Eyes
        ey = y - 33
        if self.blink:
            pygame.draw.line(surf, col, (x-5, ey), (x-2, ey), 2)
            pygame.draw.line(surf, col, (x+2, ey), (x+5, ey), 2)
        else:
            pygame.draw.circle(surf, col, (x-4, ey), 2)
            pygame.draw.circle(surf, col, (x+4, ey), 2)

        # Mouth
        if cel:
            pygame.draw.arc(surf, YELLOW, (x-5, y-24, 10, 7), math.pi, 2*math.pi, 2)
        else:
            pygame.draw.line(surf, col, (x-4, y-21), (x+4, y-21), 2)

        # BODY
        pygame.draw.line(surf, col, (x, y-18), (x, y+8), 2)

        # LEGS
        sw = int(10*math.sin(self.walk_t)) if abs(self.vx) > 0.3 else 0
        pygame.draw.line(surf, col, (x, y+8),  (x-sw, y+32), 2)
        pygame.draw.line(surf, col, (x, y+8),  (x+sw, y+32), 2)

        # ARMS — pressing pose vs walk
        if pressing:
            # One arm pushed DOWN onto button
            pygame.draw.line(surf, col, (x, y-8), (x+14*self.facing, y+12), 2)
            pygame.draw.line(surf, col, (x, y-8), (x-10*self.facing, y-2), 2)
            # Fist dot
            pygame.draw.circle(surf, YELLOW, (x+14*self.facing, y+12), 4)
        elif cel:
            # Arms up celebrating
            pygame.draw.line(surf, col, (x, y-8), (x-18, y-20+int(4*math.sin(self.walk_t*4))), 2)
            pygame.draw.line(surf, col, (x, y-8), (x+18, y-20+int(4*math.sin(self.walk_t*4+1))), 2)
        else:
            asw = int(8*math.sin(self.walk_t+math.pi)) if abs(self.vx)>0.3 else 0
            pygame.draw.line(surf, col, (x, y-8), (x-14, y+2+asw), 2)
            pygame.draw.line(surf, col, (x, y-8), (x+14, y+2-asw), 2)

        # Highlight which button the figure is on
        if self.current_btn:
            label, rect, bcol = self.current_btn
            # Glowing outline on the button
            pygame.draw.rect(surf, sym_col(label), rect, 3, border_radius=8)
            # "PRESS SPACE" tooltip above figure
            tip = F_XS.render("SPACE → press!", True, sym_col(label))
            surf.blit(tip, (x - tip.get_width()//2, y - 72))

    def rect(self):
        return pygame.Rect(self.x-13, self.y-42, 26, 74)

# ── Calculator display ─────────────────────────────────────
expr       = ""
result_str = ""
disp_flash = 0

def apply_label(label):
    """Apply a pressed button label to the expression."""
    global expr, result_str, disp_flash
    if label == "C":
        expr = ""; result_str = ""; return
    if label == "⌫":
        expr = expr[:-1]; result_str = ""; return
    if label == "=":
        try:
            safe = expr.replace("÷","/").replace("×","*").replace("−","-").replace("%","/100")
            res  = eval(safe)
            result_str = str(round(res, 8)) if isinstance(res,float) else str(res)
        except:
            result_str = "ERROR"
        return
    if label == "±":
        if expr and expr[0]=="-": expr=expr[1:]
        elif expr: expr="-"+expr
        return
    # If there's a result showing, start fresh unless appending operator
    if result_str and label not in ("+","−","×","÷","%"):
        expr = result_str
        result_str = ""
    elif result_str:
        expr = result_str
        result_str = ""
    expr += label
    disp_flash = 22

def draw_display(surf):
    pygame.draw.rect(surf, DISP_BG,    (DISP_X,DISP_Y,DISP_W,DISP_H), border_radius=10)
    pygame.draw.rect(surf, DISP_BORDER,(DISP_X,DISP_Y,DISP_W,DISP_H), 2, border_radius=10)

    # Scanlines
    for row in range(DISP_Y+3, DISP_Y+DISP_H-3, 5):
        pygame.draw.line(surf,(0,8,4),(DISP_X+3,row),(DISP_X+DISP_W-3,row))

    if result_str:
        es = F_XS.render(expr, True, GRAY)
        surf.blit(es,(DISP_X+DISP_W-es.get_width()-10, DISP_Y+8))
        rs = F_BIG.render(result_str, True, GREEN)
        surf.blit(rs,(DISP_X+DISP_W-rs.get_width()-10, DISP_Y+DISP_H-rs.get_height()-6))
    else:
        col = (90,240,130) if disp_flash>0 else (50,150,75)
        disp_text = expr if expr else "0"
        # Scroll if too long
        es = F_BIG.render(disp_text, True, col)
        if es.get_width() > DISP_W-16:
            # clip to right portion
            clip = pygame.Rect(es.get_width()-(DISP_W-20), 0, DISP_W-20, es.get_height())
            surf.blit(es, (DISP_X+8, DISP_Y+DISP_H-es.get_height()-6), clip)
        else:
            surf.blit(es,(DISP_X+DISP_W-es.get_width()-10,
                          DISP_Y+DISP_H-es.get_height()-6))

def draw_calculator(surf):
    # Body
    pygame.draw.rect(surf, CALC_BODY,   (CALC_X,CALC_Y,CALC_W,CALC_H), border_radius=20)
    pygame.draw.rect(surf, CALC_BORDER, (CALC_X,CALC_Y,CALC_W,CALC_H), 3, border_radius=20)

    # Brand
    b = F_XS.render("DIGIT KEEPER  v3.0", True, GRAY)
    surf.blit(b,(CALC_X+CALC_W//2-b.get_width()//2, CALC_Y+10))

    # Buttons (base layer — anims drawn on top)
    for label, rect, color, is_op in BTN_DATA:
        pygame.draw.rect(surf, color, rect, border_radius=8)
        pygame.draw.rect(surf, CALC_BORDER, rect, 1, border_radius=8)

        # Label color
        lc = sym_col(label)
        ls = F_SM.render(label, True, lc)
        surf.blit(ls,(rect.centerx-ls.get_width()//2,
                      rect.centery-ls.get_height()//2))

        # Small hint
        hs = F_TINY.render("←walk here", True, (55,55,78))
        surf.blit(hs,(rect.x+3, rect.y+3))

# ── Right panel ────────────────────────────────────────────
def draw_panel(surf, figure):
    px = CALC_X + CALC_W + 30
    py = CALC_Y

    # Title
    t = F_MED.render("DIGIT KEEPER 3", True, CYAN)
    surf.blit(t,(px,py))
    s = F_XS.render("Walk to a button → press SPACE!", True, GRAY)
    surf.blit(s,(px,py+36)); py+=72

    # Current standing on
    pygame.draw.rect(surf,DARK,(px,py,320,74),border_radius=10)
    pygame.draw.rect(surf,CALC_BORDER,(px,py,320,74),2,border_radius=10)
    ol=F_XS.render("STANDING ON:",True,GRAY); surf.blit(ol,(px+10,py+8))
    if figure.current_btn:
        label,_,_ = figure.current_btn
        big = F_GIANT.render(label, True, sym_col(label))
        surf.blit(big,(px+160-big.get_width()//2, py+38-big.get_height()//2))
    else:
        nd=F_SM.render("(between buttons)", True,(55,55,80))
        surf.blit(nd,(px+10,py+36))
    py+=90

    # Expression box
    pygame.draw.rect(surf,DARK,(px,py,320,52),border_radius=8)
    pygame.draw.rect(surf,CALC_BORDER,(px,py,320,52),1,border_radius=8)
    el=F_XS.render("EXPRESSION:",True,GRAY); surf.blit(el,(px+10,py+8))
    ev=F_SM.render(expr if expr else "—",True,GREEN)
    surf.blit(ev,(px+10,py+26)); py+=64

    if result_str:
        pygame.draw.rect(surf,DARK,(px,py,320,52),border_radius=8)
        pygame.draw.rect(surf,CALC_BORDER,(px,py,320,52),1,border_radius=8)
        rl=F_XS.render("RESULT:",True,GRAY); surf.blit(rl,(px+10,py+8))
        rv=F_SM.render(result_str,True,LIME := (130,255,80))
        surf.blit(rv,(px+10,py+26)); py+=64

    # Controls
    py+=6
    ct=F_SM.render("CONTROLS",True,CYAN); surf.blit(ct,(px,py)); py+=28
    controls=[
        ("← → / A D","Walk left / right"),
        ("↑ / W",     "Jump between rows"),
        ("SPACE",     "Press button you stand on"),
        ("ESC",       "Quit"),
    ]
    for key,desc in controls:
        ks=F_XS.render(key,True,YELLOW)
        ds=F_XS.render("— "+desc,True,WHITE)
        surf.blit(ks,(px,py)); surf.blit(ds,(px+118,py)); py+=22

    # Tips
    py+=12
    tips=[
        "💡 Walk onto a button to highlight it.",
        "💡 Jump up to reach row above!",
        "💡 The figure PUSHES the button down.",
        "💡 Build expressions like 7 × 8 = 56!",
        "💡 Walk to = and press SPACE to evaluate.",
    ]
    tip = tips[(pygame.time.get_ticks()//3500) % len(tips)]
    ts=F_XS.render(tip,True,(95,155,115)); surf.blit(ts,(px,py))

# ── Background ─────────────────────────────────────────────
def draw_bg(surf):
    surf.fill(BG)
    for gx in range(0,W,32): pygame.draw.line(surf,(20,20,34),(gx,0),(gx,H))
    for gy in range(0,H,32): pygame.draw.line(surf,(20,20,34),(0,gy),(W,gy))

# ── MAIN ──────────────────────────────────────────────────
figure     = Figure()
space_lock = False

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False

            if event.key == pygame.K_SPACE and not space_lock:
                label = figure.press_button()
                if label:
                    apply_label(label)
                    space_lock = True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                space_lock = False

    # Update
    keys = pygame.key.get_pressed()
    figure.handle_input(keys)
    figure.update()

    if disp_flash > 0: disp_flash -= 1

    for pa in press_anims:  pa.update()
    press_anims[:] = [p for p in press_anims if p.alive()]

    for rs in rising_syms:  rs.update()
    rising_syms[:] = [r for r in rising_syms if r.alive()]

    for pt in particles:    pt.update()
    particles[:] = [p for p in particles if p.life > 0]

    # Draw
    draw_bg(screen)
    draw_calculator(screen)

    # Press animations (over buttons, under figure)
    for pa in press_anims:
        pa.draw(screen)

    draw_display(screen)

    # Rising symbols
    for rs in rising_syms:
        rs.draw(screen)

    # Particles
    for pt in particles:
        pt.draw(screen)

    # Figure drawn last so it's on top
    figure.draw(screen)

    draw_panel(screen, figure)

    pygame.display.flip()

pygame.quit()
sys.exit()
