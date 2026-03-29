"""
╔══════════════════════════════════════════════════════════╗
║          EULER'S WRATH — A Math Battle Game              ║
║  Stick Figure vs Euler's Identity  (e^iπ + 1 = 0)        ║
║                                                          ║
║  Install:  pip install pygame                            ║
║  Run:      python math_battle.py                         ║
╚══════════════════════════════════════════════════════════╝

CONTROLS:
  Arrow Keys / WASD  — Move stick figure
  SPACE              — Fire current weapon
  1                  — Switch to Σ Sigma Gun  (Summation beam)
  2                  — Switch to ∫ Integral Gun (Area blast)
  3                  — Switch to + Basic Shot
  R                  — Restart after game over
  ESC                — Quit
"""

import pygame
import math
import random
import sys

# ─────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────
pygame.init()
pygame.font.init()

W, H = 1100, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("EULER'S WRATH — Math Battle")
clock = pygame.time.Clock()
FPS = 60

# ─────────────────────────────────────────────
#  FONTS  (falls back gracefully)
# ─────────────────────────────────────────────
def load_font(size, bold=False):
    for name in ["Consolas", "Courier New", "monospace", None]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

FONT_LG  = load_font(52, bold=True)
FONT_MD  = load_font(32, bold=True)
FONT_SM  = load_font(22)
FONT_XS  = load_font(16)
FONT_HUD = load_font(20, bold=True)

# ─────────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────────
BG_TOP    = (8,  8, 20)
BG_BOT    = (15, 5, 35)
WHITE     = (240, 240, 255)
BLACK     = (0,   0,   0)
CYAN      = (0,  220, 255)
PURPLE    = (180,  60, 255)
ORANGE    = (255, 140,  30)
RED       = (255,  50,  50)
GREEN     = (50,  255, 120)
YELLOW    = (255, 240,  60)
GRAY      = (120, 120, 150)
DARK_GRAY = (30,  30,  50)
PINK      = (255, 100, 180)

# ─────────────────────────────────────────────
#  PARTICLES
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, text=None, vx=None, vy=None, life=None, size=None):
        self.x  = x
        self.y  = y
        self.color = color
        self.text  = text
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-4, -1)
        self.life    = life  if life  is not None else random.randint(30, 70)
        self.maxlife = self.life
        self.size    = size  if size  is not None else random.randint(3, 7)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.12
        self.life -= 1

    def draw(self, surf):
        alpha = self.life / self.maxlife
        c = tuple(int(ch * alpha) for ch in self.color)
        if self.text:
            s = FONT_XS.render(self.text, True, c)
            surf.blit(s, (int(self.x), int(self.y)))
        else:
            r = max(1, int(self.size * alpha))
            pygame.draw.circle(surf, c, (int(self.x), int(self.y)), r)

particles = []

def spawn_particles(x, y, color, n=12, texts=None):
    for i in range(n):
        t = random.choice(texts) if texts else None
        particles.append(Particle(x, y, color, text=t))

# ─────────────────────────────────────────────
#  PROJECTILE BASE
# ─────────────────────────────────────────────
class Projectile:
    """Base class for all fired projectiles."""
    def __init__(self, x, y, dx, dy, owner):
        self.x, self.y  = float(x), float(y)
        self.dx, self.dy = dx, dy
        self.owner = owner   # 'player' or 'enemy'
        self.alive  = True
        self.damage = 10
        self.trail  = []

    def update(self):
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 14:
            self.trail.pop(0)
        self.x += self.dx
        self.y += self.dy
        if not (-50 < self.x < W+50 and -50 < self.y < H+50):
            self.alive = False

    def draw(self, surf):
        pass

    def rect(self):
        return pygame.Rect(self.x-6, self.y-6, 12, 12)


class SigmaShot(Projectile):
    """Σ — slow wide beam, high damage"""
    LABEL = "Σ"
    COLOR = CYAN

    def __init__(self, x, y, dx, dy, owner):
        super().__init__(x, y, dx*0.7, dy*0.7, owner)
        self.damage = 25
        self.angle  = 0
        self.expr   = f"Σn={random.randint(1,5)}^{random.randint(6,20)} n²"

    def update(self):
        super().update()
        self.angle += 8

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / len(self.trail)
            c = tuple(int(ch * alpha * 0.6) for ch in self.COLOR)
            pygame.draw.circle(surf, c, (tx, ty), max(1, int(10*alpha)))

        # Sigma glyph spinning
        s = FONT_MD.render("Σ", True, self.COLOR)
        rotated = pygame.transform.rotate(s, self.angle)
        r = rotated.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rotated, r)

        # glow ring
        pygame.draw.circle(surf, self.COLOR, (int(self.x), int(self.y)), 18, 2)


class IntegralShot(Projectile):
    """∫ — area blast, very high damage, slower"""
    LABEL = "∫"
    COLOR = PURPLE

    def __init__(self, x, y, dx, dy, owner):
        super().__init__(x, y, dx*0.5, dy*0.5, owner)
        self.damage = 40
        self.age    = 0
        self.a      = round(random.uniform(0, 1), 1)
        self.b      = round(random.uniform(2, 4), 1)

    def update(self):
        super().update()
        self.age += 1

    def draw(self, surf):
        # Wavy trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / max(len(self.trail), 1)
            w = int(6 * alpha)
            if w > 0:
                c = tuple(int(ch * alpha * 0.7) for ch in self.COLOR)
                pygame.draw.circle(surf, c, (tx, ty), w)

        # Integral symbol + bounds
        sym = FONT_MD.render("∫", True, self.COLOR)
        surf.blit(sym, (int(self.x)-10, int(self.y)-16))
        bounds = FONT_XS.render(f"{self.a}→{self.b}", True, self.COLOR)
        surf.blit(bounds, (int(self.x)+8, int(self.y)-8))

        # pulsing aura
        r = 22 + int(4 * math.sin(self.age * 0.3))
        pygame.draw.circle(surf, self.COLOR, (int(self.x), int(self.y)), r, 2)
        pygame.draw.circle(surf, tuple(c//3 for c in self.COLOR),
                           (int(self.x), int(self.y)), r-4, 1)


class BasicShot(Projectile):
    """+ simple arithmetic shot, fast"""
    LABEL = "+"
    COLOR = YELLOW

    def __init__(self, x, y, dx, dy, owner):
        super().__init__(x, y, dx*1.4, dy*1.4, owner)
        self.damage = 10
        ops = ["+", "−", "×", "÷", "²", "√"]
        self.sym = random.choice(ops)

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / max(len(self.trail), 1)
            c = tuple(int(ch * alpha * 0.8) for ch in self.COLOR)
            pygame.draw.circle(surf, c, (tx, ty), max(1, int(5*alpha)))

        s = FONT_SM.render(self.sym, True, self.COLOR)
        surf.blit(s, (int(self.x)-8, int(self.y)-8))


class EulerBeam(Projectile):
    """Enemy's e^iπ beam — sweeping arc shot"""
    COLOR = (255, 80, 80)

    def __init__(self, x, y, dx, dy):
        super().__init__(x, y, dx, dy, 'enemy')
        self.damage = 15
        self.age    = 0
        self.label  = random.choice(["e^iπ", "e^iπ+1", "eiπ=-1", "e^iθ"])

    def update(self):
        super().update()
        self.age += 1
        self.dy += 0.05   # slight gravity for arc

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / max(len(self.trail), 1)
            c = tuple(int(ch * alpha) for ch in self.COLOR)
            pygame.draw.circle(surf, c, (tx, ty), max(1, int(7*alpha)))

        # rotating formula
        ang = self.age * 5
        s = FONT_XS.render(self.label, True, self.COLOR)
        rot = pygame.transform.rotate(s, ang)
        r = rot.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rot, r)
        pygame.draw.circle(surf, self.COLOR, (int(self.x), int(self.y)), 14, 2)


# ─────────────────────────────────────────────
#  STICK FIGURE (Player)
# ─────────────────────────────────────────────
class StickFigure:
    SPEED   = 4.5
    WEAPONS = [BasicShot, SigmaShot, IntegralShot]
    W_NAMES = ["+ Basic", "Σ Sigma", "∫ Integral"]
    W_COLORS= [YELLOW, CYAN, PURPLE]
    COOLDOWNS = [12, 28, 45]   # frames between shots

    def __init__(self):
        self.x  = 160.0
        self.y  = float(H//2)
        self.hp = 150
        self.maxhp = 150
        self.weapon = 0
        self.cooldown = 0
        self.invincible = 0   # frames of i-frames after hit
        self.score = 0
        self.facing = 1   # 1=right, -1=left
        # limb animation
        self.walk_t  = 0
        self.shooting = 0

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.x -= self.SPEED; self.facing=-1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.x += self.SPEED; self.facing= 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.y -= self.SPEED
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.y += self.SPEED
        self.x = max(20, min(W//2-40, self.x))
        self.y = max(40, min(H-40,   self.y))
        self.walk_t += 0.18

        if keys[pygame.K_1]: self.weapon = 0
        if keys[pygame.K_2]: self.weapon = 1
        if keys[pygame.K_3]: self.weapon = 2

    def shoot(self):
        if self.cooldown > 0:
            return None
        self.cooldown = self.COOLDOWNS[self.weapon]
        self.shooting = 10
        cls = self.WEAPONS[self.weapon]
        p = cls(self.x+20*self.facing, self.y-5, 9*self.facing, 0, 'player')
        spawn_particles(self.x+20*self.facing, self.y-5,
                        self.W_COLORS[self.weapon], n=6)
        return p

    def update(self):
        if self.cooldown   > 0: self.cooldown   -= 1
        if self.invincible > 0: self.invincible -= 1
        if self.shooting   > 0: self.shooting   -= 1

    def take_damage(self, dmg):
        if self.invincible > 0:
            return
        self.hp = max(0, self.hp - dmg)
        self.invincible = 45
        spawn_particles(int(self.x), int(self.y), RED, n=16,
                        texts=["−"+str(dmg)])

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        blink = (self.invincible > 0 and (self.invincible // 5) % 2 == 0)
        if blink:
            return

        col = WHITE
        # head
        pygame.draw.circle(surf, col, (x, y-28), 12, 2)
        # body
        pygame.draw.line(surf, col, (x, y-16), (x, y+10), 2)
        # legs
        lsway = int(10 * math.sin(self.walk_t))
        pygame.draw.line(surf, col, (x, y+10), (x - lsway, y+32), 2)
        pygame.draw.line(surf, col, (x, y+10), (x + lsway, y+32), 2)
        # arms — shooting pose vs idle
        if self.shooting > 0:
            arm_y_off = -6
            # raised arm toward enemy
            pygame.draw.line(surf, col, (x, y-6),
                             (x + 22*self.facing, y+arm_y_off), 2)
            pygame.draw.line(surf, col, (x, y-6),
                             (x - 8*self.facing, y+6), 2)
        else:
            asway = int(8 * math.sin(self.walk_t + math.pi))
            pygame.draw.line(surf, col, (x, y-6), (x-14, y+4+asway), 2)
            pygame.draw.line(surf, col, (x, y-6), (x+14, y+4-asway), 2)

        # weapon label above head
        wname = self.W_NAMES[self.weapon]
        wcol  = self.W_COLORS[self.weapon]
        ws = FONT_XS.render(wname, True, wcol)
        surf.blit(ws, (x - ws.get_width()//2, y - 54))

    def rect(self):
        return pygame.Rect(self.x-14, self.y-40, 28, 72)


# ─────────────────────────────────────────────
#  EULER'S IDENTITY BOSS
# ─────────────────────────────────────────────
class EulerBoss:
    PHASE_NAMES = ["DORMANT", "AWAKENED", "ENRAGED", "FINAL FORM"]

    def __init__(self):
        self.x  = float(W - 160)
        self.y  = float(H // 2)
        self.hp = 300
        self.maxhp = 300
        self.phase  = 0
        self.shoot_timer  = 0
        self.move_timer   = 0
        self.target_y     = float(H // 2)
        self.shoot_pattern = 0
        self.age  = 0
        self.rage = 0    # increases as hp drops
        self.angry_text_timer = 0

        # flash when hit
        self.hit_flash = 0

    @property
    def shoot_rate(self):
        return max(18, 55 - self.phase * 10 - self.rage // 5)

    def update(self, player_y):
        self.age += 1
        if self.hit_flash > 0: self.hit_flash -= 1

        # Phase transitions
        ratio = self.hp / self.maxhp
        if   ratio > 0.66: self.phase = 0
        elif ratio > 0.33: self.phase = 1
        else:               self.phase = 2
        if self.hp <= 0:    self.phase = 3

        self.rage = int((1 - ratio) * 60)

        # Movement — hover vertically, track player
        self.move_timer += 1
        if self.move_timer > 40:
            self.target_y = player_y + random.randint(-80, 80)
            self.target_y = max(60, min(H-60, self.target_y))
            self.move_timer = 0
        self.y += (self.target_y - self.y) * 0.04

        # Horizontal drift (enraged)
        if self.phase >= 2:
            self.x = W - 160 + 30 * math.sin(self.age * 0.04)

        # Angry text flash
        if self.angry_text_timer > 0:
            self.angry_text_timer -= 1

    def shoot(self, player_x, player_y):
        """Return list of projectiles to fire."""
        shots = []
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy) or 1
        # normalised direction toward player
        ndx = dx / dist
        ndy = dy / dist
        speed = 4.5 + self.phase * 0.8

        pat = self.shoot_pattern % (3 + self.phase)
        if pat == 0:
            # Single aimed shot
            shots.append(EulerBeam(self.x-20, self.y, ndx*speed, ndy*speed))
        elif pat == 1:
            # Triple spread
            for angle_off in [-15, 0, 15]:
                rad = math.radians(angle_off)
                rdx = ndx*math.cos(rad) - ndy*math.sin(rad)
                rdy = ndx*math.sin(rad) + ndy*math.cos(rad)
                shots.append(EulerBeam(self.x-20, self.y, rdx*speed, rdy*speed))
        elif pat == 2:
            # Spiral burst (enraged only)
            for i in range(5):
                ang = math.radians(i * 72 + self.age * 3)
                shots.append(EulerBeam(self.x-20, self.y,
                                       math.cos(ang)*speed, math.sin(ang)*speed))
        elif pat == 3:
            # Aimed + 2 random
            shots.append(EulerBeam(self.x-20, self.y, ndx*speed, ndy*speed))
            for _ in range(2):
                a = random.uniform(0, 2*math.pi)
                shots.append(EulerBeam(self.x-20, self.y,
                                       math.cos(a)*speed*0.7, math.sin(a)*speed*0.7))
        self.shoot_pattern += 1
        return shots

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        self.hit_flash = 12
        self.angry_text_timer = 60
        spawn_particles(int(self.x), int(self.y), RED, n=20,
                        texts=["−"+str(dmg), "e^iπ!", "RESIST!"])

    def draw(self, surf):
        x, y = int(self.x), int(self.y)

        # glow aura
        phase_colors = [CYAN, ORANGE, RED, PINK]
        aura_col = phase_colors[self.phase]
        aura_r = 50 + int(8 * math.sin(self.age * 0.08))
        for r in range(aura_r, aura_r-20, -4):
            a_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            alpha  = max(0, int(30 * (1-(aura_r-r)/20)))
            pygame.draw.circle(a_surf, (*aura_col, alpha), (r, r), r)
            surf.blit(a_surf, (x-r, y-r))

        hit_col = WHITE if self.hit_flash > 0 else aura_col

        # ── Draw formula/entity ──────────────────────────────
        # Central symbol: e^iπ + 1 = 0
        main_sym = FONT_LG.render("e^iπ+1=0", True, hit_col)
        surf.blit(main_sym, (x - main_sym.get_width()//2,
                              y - main_sym.get_height()//2))

        # Orbiting symbols
        orbit_syms = ["π", "e", "i", "∞", "Σ", "∫"]
        for idx, sym in enumerate(orbit_syms):
            angle = self.age * 0.035 + idx * (2*math.pi/len(orbit_syms))
            radius = 70 + 10*math.sin(self.age*0.05 + idx)
            sx = x + int(radius * math.cos(angle))
            sy = y + int(radius * math.sin(angle))
            ss = FONT_SM.render(sym, True, aura_col)
            surf.blit(ss, (sx - ss.get_width()//2, sy - ss.get_height()//2))

        # Angry text
        if self.angry_text_timer > 0:
            phrases = ["YOU CAN'T DEFEAT MATH!", "e^iπ + 1 = 0 IS ETERNAL!",
                       "EULER NEVER DIES!", "FEEL THE ROTATION!", "IM IS REAL!"]
            phrase = phrases[(self.shoot_pattern // 3) % len(phrases)]
            alpha  = min(255, self.angry_text_timer * 5)
            ts = FONT_SM.render(phrase, True, RED)
            surf.blit(ts, (x - ts.get_width()//2, y - 90))

    def rect(self):
        return pygame.Rect(self.x-40, self.y-40, 80, 80)


# ─────────────────────────────────────────────
#  BACKGROUND MATH DRIFTERS
# ─────────────────────────────────────────────
class BgSymbol:
    SYMBOLS = [
        "e^iπ+1=0", "Σ", "∫", "π", "e", "i", "√−1",
        "∞", "dx", "lim", "∂", "∇", "Δ", "ℝ", "ℂ",
        "n²", "sin(x)", "cos(θ)", "ln(e)", "0!", "1=1"
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        self.x   = random.randint(0, W)
        self.y   = random.randint(-50, H+50)
        self.vy  = random.uniform(0.2, 0.8)
        self.vx  = random.uniform(-0.3, 0.3)
        self.sym = random.choice(self.SYMBOLS)
        self.alpha = random.randint(20, 70)
        self.size  = random.choice([14, 18, 22])

    def update(self):
        self.y += self.vy
        self.x += self.vx
        if self.y > H + 40:
            self.reset()
            self.y = -20

    def draw(self, surf):
        f = pygame.font.Font(None, self.size)
        s = f.render(self.sym, True,
                     (60, 60, 100))
        surf.blit(s, (int(self.x), int(self.y)))

bg_symbols = [BgSymbol() for _ in range(60)]

# ─────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────
def draw_health_bar(surf, x, y, w, h, hp, maxhp, color, label):
    pygame.draw.rect(surf, DARK_GRAY, (x, y, w, h), border_radius=4)
    fill = int(w * hp / maxhp)
    if fill > 0:
        pygame.draw.rect(surf, color, (x, y, fill, h), border_radius=4)
    pygame.draw.rect(surf, GRAY, (x, y, w, h), 2, border_radius=4)
    ls = FONT_XS.render(f"{label}  {hp}/{maxhp}", True, WHITE)
    surf.blit(ls, (x, y - 18))

def draw_hud(surf, player, boss, wave):
    # --- Player HUD ---
    draw_health_bar(surf, 20, 30, 200, 16, player.hp, player.maxhp, GREEN, "HP")

    # Weapon slots
    for i, (wn, wc) in enumerate(zip(player.W_NAMES, player.W_COLORS)):
        bx = 20 + i * 90
        by = 60
        border = 2 if player.weapon == i else 1
        col    = wc if player.weapon == i else GRAY
        pygame.draw.rect(surf, DARK_GRAY, (bx, by, 80, 24), border_radius=4)
        pygame.draw.rect(surf, col, (bx, by, 80, 24), border, border_radius=4)
        ws = FONT_XS.render(f"[{i+1}] {wn}", True, col)
        surf.blit(ws, (bx+4, by+4))

    # Cooldown bar for current weapon
    if player.cooldown > 0:
        max_cd = player.COOLDOWNS[player.weapon]
        cx = 20
        cy = 90
        cw = int(270 * (1 - player.cooldown/max_cd))
        pygame.draw.rect(surf, DARK_GRAY, (cx, cy, 270, 6), border_radius=3)
        pygame.draw.rect(surf, player.W_COLORS[player.weapon],
                         (cx, cy, cw, 6), border_radius=3)

    # Score
    ss = FONT_HUD.render(f"SCORE: {player.score}", True, YELLOW)
    surf.blit(ss, (20, H - 30))

    # --- Boss HUD ---
    phase_cols = [CYAN, ORANGE, RED, PINK]
    draw_health_bar(surf, W-320, 30, 300, 16, max(0,boss.hp), boss.maxhp,
                    phase_cols[boss.phase], "EULER")
    pn = boss.PHASE_NAMES[boss.phase]
    ps = FONT_XS.render(f"PHASE: {pn}", True, phase_cols[boss.phase])
    surf.blit(ps, (W-320, 52))

    # Controls reminder (top center)
    hint = FONT_XS.render("WASD/Arrows: Move | SPACE: Shoot | 1-2-3: Weapon", True, GRAY)
    surf.blit(hint, (W//2 - hint.get_width()//2, 8))


# ─────────────────────────────────────────────
#  SCREEN FLASH
# ─────────────────────────────────────────────
screen_flash = 0
flash_color  = WHITE

def trigger_flash(color=WHITE, strength=80):
    global screen_flash, flash_color
    screen_flash = strength
    flash_color  = color


# ─────────────────────────────────────────────
#  INTRO / STORY SEQUENCE
# ─────────────────────────────────────────────
def draw_intro(surf, t):
    """Simple animated intro telling the story."""
    surf.fill(BG_TOP)
    lines = [
        (0,   "A stick figure discovers mathematics..."),
        (90,  "They learn arithmetic: + − × ÷"),
        (180, "Then sigma:  Σ  and integrals:  ∫"),
        (270, "Combining them, they accidentally summon..."),
        (360, "   e^iπ + 1 = 0"),
        (420, "EULER'S IDENTITY AWAKENS!"),
        (490, "A battle erupts between mind and formula."),
        (570, "Press SPACE to begin the fight."),
    ]
    y0 = 160
    for start, text in lines:
        if t >= start:
            alpha = min(255, (t - start) * 6)
            color = CYAN if "e^iπ" in text else (RED if "AWAKENS" in text else WHITE)
            fs = FONT_SM.render(text, True, color)
            surf.blit(fs, (W//2 - fs.get_width()//2, y0))
        y0 += 40

    # animated stick figure on left
    sx, sy = 200, 360
    t2 = t * 0.12
    pygame.draw.circle(surf, WHITE, (sx, sy-28), 12, 2)
    pygame.draw.line(surf, WHITE, (sx, sy-16), (sx, sy+10), 2)
    lsway = int(10*math.sin(t2))
    pygame.draw.line(surf, WHITE, (sx,sy+10),(sx-lsway,sy+32),2)
    pygame.draw.line(surf, WHITE, (sx,sy+10),(sx+lsway,sy+32),2)
    pygame.draw.line(surf, WHITE, (sx,sy-6),(sx-14,sy+4+lsway),2)
    pygame.draw.line(surf, WHITE, (sx,sy-6),(sx+14,sy+4-lsway),2)

    if t >= 360:
        # Euler boss forming on right
        bx, by = W-200, 340
        col = RED if t >= 420 else ORANGE
        es = FONT_LG.render("e^iπ+1=0", True, col)
        surf.blit(es, (bx - es.get_width()//2, by - 20))
        for i, sym in enumerate(["π","e","i","∞"]):
            angle = t*0.04 + i*math.pi/2
            px2 = bx + int(50*math.cos(angle))
            py2 = by + int(50*math.sin(angle))
            ss = FONT_MD.render(sym, True, col)
            surf.blit(ss, (px2-8, py2-8))


# ─────────────────────────────────────────────
#  GAME STATES
# ─────────────────────────────────────────────
STATE_INTRO  = "intro"
STATE_FIGHT  = "fight"
STATE_WIN    = "win"
STATE_LOSE   = "lose"

state      = STATE_INTRO
intro_t    = 0
player     = StickFigure()
boss       = EulerBoss()
projectiles = []

def reset_game():
    global player, boss, projectiles, particles, state, intro_t
    player       = StickFigure()
    boss         = EulerBoss()
    projectiles  = []
    particles    = []
    state        = STATE_INTRO
    intro_t      = 0

# ─────────────────────────────────────────────
#  DRAW BACKGROUND
# ─────────────────────────────────────────────
def draw_background(surf):
    # Gradient
    for row in range(0, H, 4):
        t = row / H
        r = int(BG_TOP[0] + (BG_BOT[0]-BG_TOP[0])*t)
        g = int(BG_TOP[1] + (BG_BOT[1]-BG_TOP[1])*t)
        b = int(BG_TOP[2] + (BG_BOT[2]-BG_TOP[2])*t)
        pygame.draw.line(surf, (r,g,b), (0,row),(W,row))

    for s in bg_symbols:
        s.update()
        s.draw(surf)

    # dividing line (battlefield centre)
    pygame.draw.line(surf, (40,40,70), (W//2, 0), (W//2, H), 1)


# ─────────────────────────────────────────────
#  WIN / LOSE SCREENS
# ─────────────────────────────────────────────
def draw_end_screen(surf, won, score):
    surf.fill((0,0,0))
    if won:
        title = FONT_LG.render("YOU PROVED MATH!", True, GREEN)
        sub   = FONT_MD.render("Euler's Identity is tamed... for now.", True, CYAN)
    else:
        title = FONT_LG.render("EULER WINS!", True, RED)
        sub   = FONT_MD.render("e^iπ + 1 = 0  ...always.", True, ORANGE)

    surf.blit(title, (W//2 - title.get_width()//2, H//2 - 100))
    surf.blit(sub,   (W//2 - sub.get_width()//2,   H//2 - 30))

    sc = FONT_MD.render(f"SCORE: {score}", True, YELLOW)
    surf.blit(sc, (W//2 - sc.get_width()//2, H//2 + 40))

    restart = FONT_SM.render("Press R to play again  |  ESC to quit", True, GRAY)
    surf.blit(restart, (W//2 - restart.get_width()//2, H//2 + 110))


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
running = True
while running:
    dt = clock.tick(FPS)

    # ── EVENTS ──────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r and state in (STATE_WIN, STATE_LOSE):
                reset_game()
            if state == STATE_INTRO:
                if event.key == pygame.K_SPACE and intro_t >= 490:
                    state = STATE_FIGHT

    keys = pygame.key.get_pressed()

    # ── UPDATE ──────────────────────────────
    if state == STATE_INTRO:
        intro_t += 1
        draw_background(screen)
        draw_intro(screen, intro_t)

    elif state == STATE_FIGHT:
        player.handle_input(keys)
        player.update()

        # Player shoot
        if keys[pygame.K_SPACE]:
            shot = player.shoot()
            if shot:
                projectiles.append(shot)

        # Boss update & shoot
        boss.update(player.y)
        boss.shoot_timer += 1
        if boss.shoot_timer >= boss.shoot_rate:
            boss.shoot_timer = 0
            new_shots = boss.shoot(player.x, player.y)
            projectiles.extend(new_shots)

        # Update all projectiles
        for p in projectiles:
            p.update()

        # Collision: player shots vs boss
        for p in [pp for pp in projectiles if pp.owner=='player' and pp.alive]:
            if p.rect().colliderect(boss.rect()):
                boss.take_damage(p.damage)
                player.score += p.damage
                p.alive = False
                trigger_flash(RED, 40)

        # Collision: boss shots vs player
        for p in [pp for pp in projectiles if pp.owner=='enemy' and pp.alive]:
            if p.rect().colliderect(player.rect()):
                player.take_damage(p.damage)
                p.alive = False
                trigger_flash(WHITE, 30)

        # Remove dead projectiles
        projectiles = [p for p in projectiles if p.alive]

        # Particles
        for pt in particles: pt.update()
        particles = [pt for pt in particles if pt.life > 0]

        # Win/lose check
        if boss.hp <= 0:
            state = STATE_WIN
            spawn_particles(int(boss.x), int(boss.y), GREEN, 60)
        if player.hp <= 0:
            state = STATE_LOSE

        # ── DRAW ─────────────────────────────
        draw_background(screen)
        boss.draw(screen)
        player.draw(screen)

        for p in projectiles:
            p.draw(screen)

        for pt in particles:
            pt.draw(screen)

        draw_hud(screen, player, boss, 1)

        # Screen flash effect
        if screen_flash > 0:
            fs = pygame.Surface((W, H), pygame.SRCALPHA)
            fs.fill((*flash_color, min(180, screen_flash * 2)))
            screen.blit(fs, (0, 0))
            screen_flash = max(0, screen_flash - 5)

    elif state in (STATE_WIN, STATE_LOSE):
        draw_end_screen(screen, state == STATE_WIN, player.score)

    pygame.display.flip()

pygame.quit()
sys.exit()
