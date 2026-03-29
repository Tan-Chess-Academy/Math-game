python3 digit_keeper2.pypython3 digit_keeper2.py"""
╔══════════════════════════════════════════════════════════╗
║         DIGIT KEEPER 2 — Lives in the Display!           ║
║                                                          ║
║  Run:  python3 digit_keeper2.py                          ║
╚══════════════════════════════════════════════════════════╝

CONTROLS:
  0–9         — Pick up that digit
  + - * /     — Pick up that operator symbol
  WASD/Arrows — Move inside the display screen
  SPACE       — Toss held symbol
  C           — Drop symbol
  ENTER       — Evaluate expression on screen
  ESC         — Quit
"""

import pygame
import math
import random
import sys

pygame.init()

W, H = 980, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DIGIT KEEPER 2 — Display World")
clock  = pygame.time.Clock()
FPS    = 60

# ── Fonts ──────────────────────────────────────────────────
def fnt(size, bold=False):
    for name in ["Consolas", "Courier New", "monospace", None]:
        try: return pygame.font.SysFont(name, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

F_HUGE  = fnt(96,  bold=True)
F_BIG   = fnt(56,  bold=True)
F_MED   = fnt(34,  bold=True)
F_SM    = fnt(22,  bold=True)
F_XS    = fnt(15)
F_TINY  = fnt(12)

# ── Palette ────────────────────────────────────────────────
BG          = (14, 14, 22)
CALC_BODY   = (24, 24, 38)
CALC_BORDER = (55, 55, 85)
DISP_BG     = (8,  22, 14)
DISP_BORDER = (40, 140, 70)
BTN_NUM     = (38, 38, 58)
BTN_OP      = (55, 35, 75)
BTN_EQ      = (25, 85, 55)
BTN_CLR     = (85, 28, 38)
BTN_HOVER   = (70, 70,100)
WHITE       = (238,242,255)
GREEN       = (70, 255,130)
CYAN        = (0,  210,255)
YELLOW      = (255,228, 50)
ORANGE      = (255,148, 35)
RED         = (255, 65, 65)
PURPLE      = (175, 75,255)
GRAY        = (110,110,145)
DARK        = (18,  18, 30)
PINK        = (255,110,180)

# ── Calculator geometry ────────────────────────────────────
CALC_X, CALC_Y = 60, 40
CALC_W, CALC_H = 420, 620

# Display screen — TALL so figure can live in it
DISP_X = CALC_X + 18
DISP_Y = CALC_Y + 28
DISP_W = CALC_W - 36
DISP_H = 220          # tall display — this is the figure's world

# Button grid starts below display
BTN_AREA_Y = DISP_Y + DISP_H + 18
BTN_W, BTN_H, BTN_GAP = 82, 58, 7

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
    x = CALC_X + 18 + col*(BTN_W+BTN_GAP)
    y = BTN_AREA_Y   + row*(BTN_H+BTN_GAP)
    return pygame.Rect(x, y, BTN_W, BTN_H)

# Symbol colour map
SYM_COLORS = {
    "+": GREEN,  "−": CYAN,  "×": ORANGE, "÷": PURPLE,
    "%": PINK,   "±": YELLOW,"=": WHITE,
    "0":YELLOW,"1":YELLOW,"2":YELLOW,"3":YELLOW,"4":YELLOW,
    "5":YELLOW,"6":YELLOW,"7":YELLOW,"8":YELLOW,"9":YELLOW,
    ".": WHITE,
}

def sym_color(s):
    return SYM_COLORS.get(s, WHITE)

# ── Particles ──────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, col, text=None, vx=None, vy=None, life=55, size=5):
        self.x,self.y = float(x),float(y)
        self.col  = col
        self.text = text
        self.vx = vx if vx is not None else random.uniform(-2.5,2.5)
        self.vy = vy if vy is not None else random.uniform(-4, -.5)
        self.life = self.maxlife = life
        self.size = size
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.vy+=0.14; self.life-=1
    def draw(self,surf):
        a = self.life/self.maxlife
        c = tuple(int(ch*a) for ch in self.col)
        if self.text:
            s = F_SM.render(self.text,True,c); surf.blit(s,(int(self.x),int(self.y)))
        else:
            r=max(1,int(self.size*a))
            pygame.draw.circle(surf,c,(int(self.x),int(self.y)),r)

particles=[]
def burst(x,y,col,n=14,texts=None):
    for _ in range(n):
        t=random.choice(texts) if texts else None
        particles.append(Particle(x,y,col,text=t))

# ── Flying symbol (tossed) ─────────────────────────────────
class FlyingSymbol:
    def __init__(self,x,y,sym,vx,vy):
        self.x,self.y=float(x),float(y)
        self.sym=sym; self.vx=vx; self.vy=vy
        self.angle=0; self.spin=random.uniform(-9,9)
        self.alive=True; self.age=0
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.vy+=0.35
        self.angle+=self.spin; self.age+=1
        # bounce inside display
        if self.x<DISP_X+8:      self.vx=abs(self.vx)*0.7
        if self.x>DISP_X+DISP_W-8: self.vx=-abs(self.vx)*0.7
        if self.y>DISP_Y+DISP_H-14: self.vy=-abs(self.vy)*0.55; self.y=DISP_Y+DISP_H-14
        if self.age>100: self.alive=False
    def draw(self,surf):
        a=max(0,1-self.age/100)
        col=tuple(int(ch*a) for ch in sym_color(self.sym))
        s=F_BIG.render(self.sym,True,col)
        rot=pygame.transform.rotate(s,self.angle)
        r=rot.get_rect(center=(int(self.x),int(self.y)))
        surf.blit(rot,r)

flying=[]

# ── Stick Figure (lives INSIDE the display) ────────────────
class Figure:
    SPEED = 3.2

    # World boundaries = display screen interior
    LEFT  = DISP_X + 14
    RIGHT = DISP_X + DISP_W - 14
    TOP   = DISP_Y + 10
    BOT   = DISP_Y + DISP_H - 12   # floor of display

    def __init__(self):
        self.x   = float(DISP_X + DISP_W//2)
        self.y   = float(self.BOT - 36)
        self.vx  = 0.0
        self.vy  = 0.0
        self.on_ground = True
        self.walk_t    = 0.0
        self.facing    = 1
        self.held      = None    # symbol/digit string
        self.held_col  = WHITE
        self.dig_scale = 1.0
        self.celebrate = 0
        self.blink     = 0
        self.jump_lock = False

    def handle_input(self, keys):
        moved = False
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.vx=-self.SPEED; self.facing=-1; moved=True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx= self.SPEED; self.facing= 1; moved=True
        else:
            self.vx*=0.65

        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground and not self.jump_lock:
            self.vy=-9.5
            self.on_ground=False
            self.jump_lock=True
            burst(int(self.x),int(self.BOT),CYAN,n=7)
        if not (keys[pygame.K_UP] or keys[pygame.K_w]):
            self.jump_lock=False

        if moved: self.walk_t+=0.2

    def update(self):
        self.x += self.vx
        self.vy += 0.48
        self.y  += self.vy

        # Clamp x
        self.x = max(self.LEFT, min(self.RIGHT, self.x))

        # Floor
        if self.y >= self.BOT - 36:
            self.y = self.BOT - 36
            self.vy = 0
            self.on_ground = True

        # Ceiling
        if self.y - 40 < self.TOP:
            self.y  = self.TOP + 40
            self.vy = abs(self.vy)*0.3

        if self.dig_scale > 1.0:
            self.dig_scale = max(1.0, self.dig_scale - 0.055)
        if self.celebrate > 0: self.celebrate -= 1
        if self.blink > 0:     self.blink -= 1
        if random.random() < 0.004: self.blink = 8

    def pick(self, sym):
        self.held      = sym
        self.held_col  = sym_color(sym)
        self.dig_scale = 1.7
        self.celebrate = 45
        burst(int(self.x), int(self.y)-50, self.held_col, n=18,
              texts=[sym,"!","✦"])

    def toss(self):
        if not self.held: return
        flying.append(FlyingSymbol(
            self.x + 22*self.facing, self.y-24,
            self.held, 7*self.facing, -7))
        burst(int(self.x),int(self.y)-24,self.held_col,n=10)
        self.held = None

    def drop(self):
        if self.held:
            burst(int(self.x),int(self.y),RED,n=8)
        self.held = None

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        cel   = self.celebrate > 0

        # shadow on display floor
        pygame.draw.ellipse(surf,(20,50,28),(x-13,int(self.BOT)-8,26,7))

        col = WHITE

        # HEAD
        pygame.draw.circle(surf, col, (x, y-28), 11, 2)
        # eyes
        ey = y-31
        if self.blink:
            pygame.draw.line(surf,col,(x-5,ey),(x-2,ey),2)
            pygame.draw.line(surf,col,(x+2,ey),(x+5,ey),2)
        else:
            pygame.draw.circle(surf,col,(x-4,ey),2)
            pygame.draw.circle(surf,col,(x+4,ey),2)
        # mouth
        if cel:
            pygame.draw.arc(surf,YELLOW,(x-5,y-22,10,7),math.pi,2*math.pi,2)
        else:
            pygame.draw.line(surf,col,(x-4,y-20),(x+4,y-20),2)

        # BODY
        pygame.draw.line(surf,col,(x,y-17),(x,y+10),2)

        # LEGS
        sw = int(10*math.sin(self.walk_t)) if abs(self.vx)>0.3 else 0
        pygame.draw.line(surf,col,(x,y+10),(x-sw,y+34),2)
        pygame.draw.line(surf,col,(x,y+10),(x+sw,y+34),2)

        # ARMS + held symbol
        if self.held:
            # arms raised
            lift = -12 if not cel else -18+int(5*math.sin(self.walk_t*3))
            pygame.draw.line(surf,col,(x,y-6),(x-18,y+lift),2)
            pygame.draw.line(surf,col,(x,y-6),(x+18,y+lift),2)

            # glow halo
            sc   = self.dig_scale
            hcol = self.held_col
            gsurf = pygame.Surface((80,80), pygame.SRCALPHA)
            pygame.draw.circle(gsurf,(hcol[0],hcol[1],hcol[2],55),(40,40),36)
            surf.blit(gsurf,(x-40, y-106))

            # symbol
            sym_surf = F_BIG.render(self.held, True, hcol)
            if sc != 1.0:
                nw=int(sym_surf.get_width()*sc)
                nh=int(sym_surf.get_height()*sc)
                sym_surf=pygame.transform.scale(sym_surf,(nw,nh))
            surf.blit(sym_surf,(x-sym_surf.get_width()//2, y-84-sym_surf.get_height()//2))

            # orbiting sparkles when celebrating
            if cel:
                for i in range(5):
                    ang=self.walk_t*4+i*2*math.pi/5
                    sx2=x+int(30*math.cos(ang))
                    sy2=y-82+int(12*math.sin(ang))
                    pygame.draw.circle(surf,hcol,(sx2,sy2),3)
        else:
            # idle/walk arms
            asw = int(8*math.sin(self.walk_t+math.pi)) if abs(self.vx)>0.3 else 0
            pygame.draw.line(surf,col,(x,y-6),(x-14,y+4+asw),2)
            pygame.draw.line(surf,col,(x,y-6),(x+14,y+4-asw),2)

    def rect(self):
        return pygame.Rect(self.x-13,self.y-40,26,74)

# ── Display content (expression) ──────────────────────────
expr        = ""
result_str  = ""
disp_flash  = 0
active_btn  = None
btn_flash   = 0

def draw_display(surf, figure):
    """Draw the display screen — the figure's world."""
    # Background
    pygame.draw.rect(surf, DISP_BG,
                     (DISP_X, DISP_Y, DISP_W, DISP_H), border_radius=10)
    pygame.draw.rect(surf, DISP_BORDER,
                     (DISP_X, DISP_Y, DISP_W, DISP_H), 2, border_radius=10)

    # Scanline effect (subtle)
    for row in range(DISP_Y+2, DISP_Y+DISP_H-2, 4):
        pygame.draw.line(surf,(0,0,0,30),(DISP_X+2,row),(DISP_X+DISP_W-2,row))

    # Floor line inside display
    pygame.draw.line(surf,(40,100,55),
                     (DISP_X+10, figure.BOT+2),(DISP_X+DISP_W-10, figure.BOT+2),1)

    # Expression or result (shown in top-right corner of display)
    if result_str:
        # Show expression small, result big
        es = F_XS.render(expr, True, GRAY)
        surf.blit(es,(DISP_X+DISP_W-es.get_width()-8, DISP_Y+6))
        rs = F_MED.render(result_str, True, GREEN)
        surf.blit(rs,(DISP_X+DISP_W-rs.get_width()-8, DISP_Y+22))
    else:
        col = (100,230,130) if disp_flash>0 else (55,160,80)
        es = F_SM.render(expr if expr else "0", True, col)
        surf.blit(es,(DISP_X+DISP_W-es.get_width()-8, DISP_Y+8))

    # Flying symbols inside display
    for fs in flying:
        fs.draw(surf)

    # Particles clipped to display region
    # (drawn globally, just look natural)

    # Stick figure
    figure.draw(surf)

    # Tiny label
    lbl = F_TINY.render("DISPLAY — FIGURE'S WORLD", True, (40,90,55))
    surf.blit(lbl,(DISP_X+4, DISP_Y+DISP_H-14))

def draw_calculator(surf):
    # Body
    pygame.draw.rect(surf,CALC_BODY,(CALC_X,CALC_Y,CALC_W,CALC_H),border_radius=18)
    pygame.draw.rect(surf,CALC_BORDER,(CALC_X,CALC_Y,CALC_W,CALC_H),3,border_radius=18)

    # Brand
    b=F_XS.render("DIGIT KEEPER  v2.0", True, GRAY)
    surf.blit(b,(CALC_X+CALC_W//2-b.get_width()//2, CALC_Y+8))

    # Buttons
    for label,col,row,color,is_op in BUTTONS:
        r=btn_rect(col,row)
        lit=(active_btn==label and btn_flash>0)
        c=tuple(min(255,ch+40) for ch in color) if lit else color
        pygame.draw.rect(surf,c,r,border_radius=7)
        pygame.draw.rect(surf,CALC_BORDER,r,1,border_radius=7)

        # Label colour
        if label in ("+","−","×","÷","%","±"): lc=CYAN
        elif label=="=":                         lc=GREEN
        elif label in ("C","⌫"):                lc=RED
        else:                                    lc=YELLOW if label.isdigit() else WHITE
        ls=F_SM.render(label,True,lc)
        surf.blit(ls,(r.centerx-ls.get_width()//2, r.centery-ls.get_height()//2))

        if label.isdigit() or label in "+-*/":
            hs=F_TINY.render(f"[{label}]",True,(70,70,100))
            surf.blit(hs,(r.x+3,r.y+3))

# ── Right info panel ───────────────────────────────────────
def draw_panel(surf, figure):
    px = CALC_X + CALC_W + 35
    py = CALC_Y

    # Title
    t=F_MED.render("DIGIT KEEPER 2", True, CYAN)
    surf.blit(t,(px,py))
    s=F_XS.render("The figure lives in the display!", True, GRAY)
    surf.blit(s,(px,py+36))

    # Held symbol showcase
    py+=70
    pygame.draw.rect(surf,DARK,(px,py,360,120),border_radius=10)
    pygame.draw.rect(surf,CALC_BORDER,(px,py,360,120),2,border_radius=10)
    hl=F_XS.render("HOLDING:", True, GRAY)
    surf.blit(hl,(px+12,py+10))
    if figure.held:
        big=F_HUGE.render(figure.held, True, sym_color(figure.held))
        surf.blit(big,(px+180-big.get_width()//2, py+60-big.get_height()//2))
        nm=F_XS.render(_sym_name(figure.held), True, sym_color(figure.held))
        surf.blit(nm,(px+12,py+98))
    else:
        nd=F_SM.render("nothing", True, (55,55,80))
        surf.blit(nd,(px+180-nd.get_width()//2, py+52))

    # Controls
    py+=136
    ct=F_SM.render("CONTROLS", True, CYAN)
    surf.blit(ct,(px,py)); py+=28
    controls=[
        ("0 – 9",        "Pick up digit"),
        ("+ - * /",      "Pick up operator"),
        ("← → / A D",   "Walk in display"),
        ("↑ / W",        "Jump"),
        ("SPACE",        "Toss symbol"),
        ("C",            "Drop symbol"),
        ("ENTER",        "Evaluate expression"),
        ("⌫ BACKSPACE",  "Delete last char"),
        ("ESC",          "Quit"),
    ]
    for key,desc in controls:
        ks=F_XS.render(key,True,YELLOW)
        ds=F_XS.render("— "+desc,True,WHITE)
        surf.blit(ks,(px,py)); surf.blit(ds,(px+130,py)); py+=20

    # Expression box
    py+=10
    pygame.draw.rect(surf,DARK,(px,py,360,36),border_radius=6)
    pygame.draw.rect(surf,CALC_BORDER,(px,py,360,36),1,border_radius=6)
    el=F_XS.render("EXPR:",True,GRAY); surf.blit(el,(px+8,py+10))
    ev=F_SM.render(expr if expr else "—",True,GREEN)
    surf.blit(ev,(px+60,py+8))

    if result_str:
        py+=44
        pygame.draw.rect(surf,DARK,(px,py,360,36),border_radius=6)
        pygame.draw.rect(surf,CALC_BORDER,(px,py,360,36),1,border_radius=6)
        rl=F_XS.render("RESULT:",True,GRAY); surf.blit(rl,(px+8,py+10))
        rv=F_SM.render(result_str,True,GREEN); surf.blit(rv,(px+80,py+8))

def _sym_name(s):
    names={"+":"ADDITION","−":"SUBTRACTION","×":"MULTIPLICATION",
           "÷":"DIVISION","%":"MODULO","±":"SIGN FLIP","=":"EQUALS",
           ".":"DECIMAL POINT"}
    if s.isdigit(): return f"DIGIT  {s}"
    return names.get(s, s)

# ── Background ─────────────────────────────────────────────
def draw_bg(surf):
    surf.fill(BG)
    for gx in range(0,W,30): pygame.draw.line(surf,(22,22,36),(gx,0),(gx,H))
    for gy in range(0,H,30): pygame.draw.line(surf,(22,22,36),(0,gy),(W,gy))

# ── MAIN ──────────────────────────────────────────────────
figure = Figure()

running=True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False

        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: running=False

            # Digits
            elif event.unicode in "0123456789":
                d=event.unicode
                figure.pick(d)
                expr+=d; result_str=""; disp_flash=20
                active_btn=d; btn_flash=18

            # Operators via keyboard
            elif event.unicode=="+":
                figure.pick("+"); expr+="+"; result_str=""; disp_flash=20
                active_btn="+"; btn_flash=18
            elif event.unicode=="-":
                figure.pick("−"); expr+="−"; result_str=""; disp_flash=20
                active_btn="−"; btn_flash=18
            elif event.unicode=="*":
                figure.pick("×"); expr+="×"; result_str=""; disp_flash=20
                active_btn="×"; btn_flash=18
            elif event.unicode=="/":
                figure.pick("÷"); expr+="÷"; result_str=""; disp_flash=20
                active_btn="÷"; btn_flash=18
            elif event.unicode=="%":
                figure.pick("%"); expr+="%"; result_str=""; disp_flash=20
                active_btn="%"; btn_flash=18
            elif event.unicode==".":
                figure.pick("."); expr+="."; result_str=""; disp_flash=20
                active_btn="."; btn_flash=18

            # Toss
            elif event.key==pygame.K_SPACE:
                figure.toss()

            # Drop / clear
            elif event.key==pygame.K_c:
                figure.drop(); expr=""; result_str=""
                active_btn="C"; btn_flash=18
                burst(int(figure.x),int(figure.y)-20,RED,n=12)

            # Backspace
            elif event.key==pygame.K_BACKSPACE:
                expr=expr[:-1]; result_str=""
                active_btn="⌫"; btn_flash=18

            # Evaluate
            elif event.key==pygame.K_RETURN:
                try:
                    safe=expr.replace("÷","/").replace("×","*").replace("−","-")
                    res=eval(safe)
                    result_str=str(round(res,8)) if isinstance(res,float) else str(res)
                    active_btn="="; btn_flash=22
                    burst(int(figure.x),int(figure.y)-40,GREEN,n=22,
                          texts=["=",result_str,"✓"])
                except:
                    result_str="ERROR"
                    burst(int(figure.x),int(figure.y)-30,RED,n=10,texts=["ERR!"])

    # Update
    keys=pygame.key.get_pressed()
    figure.handle_input(keys)
    figure.update()

    if btn_flash>0:  btn_flash-=1
    else:            active_btn=None
    if disp_flash>0: disp_flash-=1

    for fs in flying:   fs.update()
    flying[:]=[fs for fs in flying if fs.alive]

    for pt in particles: pt.update()
    particles[:]=[pt for pt in particles if pt.life>0]

    # Draw
    draw_bg(screen)
    draw_calculator(screen)
    draw_display(screen, figure)   # display is drawn ON TOP of calc body

    for pt in particles:
        pt.draw(screen)

    draw_panel(screen, figure)

    pygame.display.flip()

pygame.quit()
sys.exit()
