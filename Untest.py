import pygame
import sys
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 500, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stick Figure Calculator")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
GRAY = (150, 150, 150)
GREEN = (50, 200, 50)
BLUE = (50, 100, 200)
RED = (200, 50, 50)
YELLOW = (255, 220, 0)
ORANGE = (255, 140, 0)
SKIN = (255, 200, 150)
DARK_GREEN = (0, 150, 0)
BUTTON_COLOR = (70, 70, 120)
BUTTON_HOVER = (100, 100, 180)
BUTTON_PRESSED = (255, 200, 0)
DISPLAY_BG = (20, 40, 20)
DISPLAY_TEXT = (0, 255, 80)
CALC_BG = (40, 40, 60)
CALC_BORDER = (80, 80, 120)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Fonts
font_large = pygame.font.SysFont("monospace", 48, bold=True)
font_medium = pygame.font.SysFont("monospace", 28, bold=True)
font_small = pygame.font.SysFont("monospace", 18)
font_tiny = pygame.font.SysFont("monospace", 14)

# Calculator layout
CALC_X = 50
CALC_Y = 20
CALC_W = 400
CALC_H = 660

# Display area
DISPLAY_X = CALC_X + 20
DISPLAY_Y = CALC_Y + 30
DISPLAY_W = CALC_W - 40
DISPLAY_H = 80

# Button grid area (where stick figure lives)
ARENA_X = CALC_X + 10
ARENA_Y = CALC_Y + 260
ARENA_W = CALC_W - 20
ARENA_H = 380

# Button definitions: (label, col, row)
BUTTONS = []
button_labels = [
    ['7', '8', '9'],
    ['4', '5', '6'],
    ['1', '2', '3'],
    [' ', '0', ' '],
]

BTN_W = 80
BTN_H = 60
BTN_MARGIN = 10
BTN_START_X = CALC_X + 30
BTN_START_Y = ARENA_Y + 20

button_rects = {}
button_positions = {}  # center positions of buttons

for row_i, row in enumerate(button_labels):
    for col_i, label in enumerate(row):
        if label.strip() == '':
            continue
        bx = BTN_START_X + col_i * (BTN_W + BTN_MARGIN)
        by = BTN_START_Y + row_i * (BTN_H + BTN_MARGIN)
        rect = pygame.Rect(bx, by, BTN_W, BTN_H)
        button_rects[label] = rect
        button_positions[label] = (bx + BTN_W // 2, by + BTN_H // 2)

# Stick figure class
class StickFigure:
    def __init__(self):
        self.x = ARENA_X + ARENA_W // 2
        self.y = ARENA_Y + ARENA_H - 60
        self.target_x = self.x
        self.target_y = self.y
        self.speed = 5
        self.moving = False
        self.pressing = False
        self.press_timer = 0
        self.press_key = None
        self.walk_frame = 0
        self.walk_anim = 0
        self.direction = 1  # 1 = right, -1 = left
        self.idle_anim = 0
        self.head_radius = 14
        self.body_len = 30
        self.arm_len = 20
        self.leg_len = 25
        self.bounce = 0
        self.expression = "happy"  # happy, excited, working
        self.blink_timer = 0
        self.blink = False
        self.trail = []

    def set_target(self, tx, ty, key):
        self.target_x = tx
        self.target_y = ty - self.head_radius - self.body_len - self.leg_len + 10
        self.moving = True
        self.press_key = key
        self.expression = "excited"
        # Add trail effect
        self.trail = []

    def update(self):
        self.idle_anim += 0.05
        self.blink_timer += 1
        if self.blink_timer > 120:
            self.blink = True
            if self.blink_timer > 125:
                self.blink = False
                self.blink_timer = 0

        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx*dx + dy*dy)

            # Add trail
            if len(self.trail) < 8:
                self.trail.append((self.x, self.y + 30))
            else:
                self.trail.pop(0)
                self.trail.append((self.x, self.y + 30))

            if dist < self.speed:
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
                self.pressing = True
                self.press_timer = 30
                self.walk_frame = 0
                self.expression = "working"
                self.trail = []
            else:
                move_x = (dx / dist) * self.speed
                move_y = (dy / dist) * self.speed
                self.x += move_x
                self.y += move_y
                self.walk_anim += 0.2
                self.walk_frame = int(self.walk_anim) % 4

                if dx > 0:
                    self.direction = 1
                else:
                    self.direction = -1

        if self.pressing:
            self.press_timer -= 1
            if self.press_timer <= 0:
                self.pressing = False
                self.expression = "happy"

        # Idle bounce
        if not self.moving and not self.pressing:
            self.bounce = math.sin(self.idle_anim) * 3

    def draw(self, surface):
        x = int(self.x)
        y = int(self.y + self.bounce)

        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.3)
            radius = max(2, int(4 * (i / len(self.trail))))
            trail_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (100, 200, 255, alpha), (radius, radius), radius)
            surface.blit(trail_surf, (int(tx) - radius, int(ty) - radius))

        hr = self.head_radius
        bl = self.body_len
        al = self.arm_len
        ll = self.leg_len

        head_y = y
        body_top = y + hr
        body_bot = y + hr + bl

        # Walking animation
        walk = self.walk_frame
        if self.moving:
            leg_angle_l = math.sin(self.walk_anim) * 0.6
            leg_angle_r = -math.sin(self.walk_anim) * 0.6
            arm_angle_l = -math.sin(self.walk_anim) * 0.5
            arm_angle_r = math.sin(self.walk_anim) * 0.5
        elif self.pressing:
            # Pressing animation - lean forward and press
            t = 1 - (self.press_timer / 30)
            leg_angle_l = 0.2
            leg_angle_r = -0.1
            arm_angle_l = -0.8 + t * 0.5
            arm_angle_r = -1.2 + t * 0.5
        else:
            leg_angle_l = math.sin(self.idle_anim * 0.5) * 0.1
            leg_angle_r = -math.sin(self.idle_anim * 0.5) * 0.1
            arm_angle_l = math.sin(self.idle_anim * 0.7) * 0.2
            arm_angle_r = -math.sin(self.idle_anim * 0.7) * 0.2

        # Shadow
        shadow_surf = pygame.Surface((50, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, 50, 15))
        surface.blit(shadow_surf, (x - 25, body_bot + ll - 8))

        # Draw legs
        lx1 = x - 8
        lx2 = x + 8

        # Left leg
        lleg_end_x = lx1 + math.sin(leg_angle_l) * ll * self.direction
        lleg_end_y = body_bot + math.cos(leg_angle_l) * ll
        pygame.draw.line(surface, BLACK, (lx1, body_bot), (int(lleg_end_x), int(lleg_end_y)), 3)
        # Foot
        pygame.draw.line(surface, BLACK,
                        (int(lleg_end_x), int(lleg_end_y)),
                        (int(lleg_end_x + 8 * self.direction), int(lleg_end_y)), 3)

        # Right leg
        rleg_end_x = lx2 + math.sin(leg_angle_r) * ll * self.direction
        rleg_end_y = body_bot + math.cos(leg_angle_r) * ll
        pygame.draw.line(surface, BLACK, (lx2, body_bot), (int(rleg_end_x), int(rleg_end_y)), 3)
        # Foot
        pygame.draw.line(surface, BLACK,
                        (int(rleg_end_x), int(rleg_end_y)),
                        (int(rleg_end_x + 8 * self.direction), int(rleg_end_y)), 3)

        # Draw body
        pygame.draw.line(surface, BLACK, (x, body_top), (x, body_bot), 3)

        # Draw arms
        # Left arm
        larm_end_x = x + math.sin(arm_angle_l - 0.3) * al * self.direction
        larm_end_y = body_top + 10 + math.cos(arm_angle_l - 0.3) * al * 0.7
        pygame.draw.line(surface, BLACK, (x, body_top + 8), (int(larm_end_x), int(larm_end_y)), 3)

        # Right arm
        rarm_end_x = x + math.sin(arm_angle_r + 0.3) * al * self.direction
        rarm_end_y = body_top + 10 + math.cos(arm_angle_r + 0.3) * al * 0.7
        pygame.draw.line(surface, BLACK, (x, body_top + 8), (int(rarm_end_x), int(rarm_end_y)), 3)

        # Draw head
        pygame.draw.circle(surface, SKIN, (x, head_y), hr)
        pygame.draw.circle(surface, BLACK, (x, head_y), hr, 2)

        # Hair
        pygame.draw.arc(surface, (80, 40, 0),
                       (x - hr, head_y - hr, hr*2, hr*2),
                       math.pi * 0.1, math.pi * 0.9, 5)

        # Eyes
        eye_offset = 5
        if self.blink:
            pygame.draw.line(surface, BLACK,
                           (x - eye_offset - 3, head_y - 2),
                           (x - eye_offset + 3, head_y - 2), 2)
            pygame.draw.line(surface, BLACK,
                           (x + eye_offset - 3, head_y - 2),
                           (x + eye_offset + 3, head_y - 2), 2)
        else:
            if self.expression == "excited" or self.pressing:
                # Star eyes
                pygame.draw.circle(surface, YELLOW, (x - eye_offset, head_y - 2), 4)
                pygame.draw.circle(surface, YELLOW, (x + eye_offset, head_y - 2), 4)
                pygame.draw.circle(surface, BLACK, (x - eye_offset, head_y - 2), 2)
                pygame.draw.circle(surface, BLACK, (x + eye_offset, head_y - 2), 2)
            else:
                pygame.draw.circle(surface, BLACK, (x - eye_offset, head_y - 2), 3)
                pygame.draw.circle(surface, BLACK, (x + eye_offset, head_y - 2), 3)
                pygame.draw.circle(surface, WHITE, (x - eye_offset + 1, head_y - 3), 1)
                pygame.draw.circle(surface, WHITE, (x + eye_offset + 1, head_y - 3), 1)

        # Mouth
        if self.expression == "happy":
            pygame.draw.arc(surface, BLACK,
                           (x - 7, head_y + 2, 14, 8),
                           math.pi, 2 * math.pi, 2)
        elif self.expression == "excited":
            pygame.draw.ellipse(surface, BLACK, (x - 5, head_y + 3, 10, 7))
            pygame.draw.ellipse(surface, RED, (x - 4, head_y + 4, 8, 5))
        elif self.expression == "working":
            # Tongue out
            pygame.draw.arc(surface, BLACK,
                           (x - 6, head_y + 2, 12, 7),
                           math.pi, 2 * math.pi, 2)
            pygame.draw.ellipse(surface, RED, (x - 3, head_y + 7, 6, 5))

        # Shirt color
        shirt_color = (50, 100, 200)
        pygame.draw.rect(surface, shirt_color,
                        (x - 8, body_top + 2, 16, bl - 4), border_radius=3)

        # Little number badge on shirt
        if self.press_key:
            badge_surf = font_tiny.render(self.press_key, True, WHITE)
            surface.blit(badge_surf, (x - 5, body_top + 8))

# Particle class for button press effects
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = (pygame.math.Vector2(1, 0).rotate(
            pygame.time.get_ticks() % 360)).x * 3 + (hash((x, y, pygame.time.get_ticks())) % 10 - 5) * 0.5
        import random
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -1)
        self.color = color
        self.life = random.randint(20, 40)
        self.max_life = self.life
        self.radius = random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        r = max(1, int(self.radius * (self.life / self.max_life)))
        surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (r, r), r)
        surface.blit(surf, (int(self.x) - r, int(self.y) - r))

# Number display
class Calculator:
    def __init__(self):
        self.display_value = "0"
        self.pressed_button = None
        self.press_anim = {}  # button: timer
        self.flash_timer = 0

    def press(self, digit):
        if self.display_value == "0":
            self.display_value = digit
        elif len(self.display_value) < 12:
            self.display_value += digit
        self.pressed_button = digit
        self.press_anim[digit] = 20
        self.flash_timer = 10

    def update(self):
        for key in list(self.press_anim.keys()):
            self.press_anim[key] -= 1
            if self.press_anim[key] <= 0:
                del self.press_anim[key]
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface):
        # Calculator body
        body_rect = pygame.Rect(CALC_X, CALC_Y, CALC_W, CALC_H)
        pygame.draw.rect(surface, CALC_BG, body_rect, border_radius=20)
        pygame.draw.rect(surface, CALC_BORDER, body_rect, 3, border_radius=20)

        # Decorative top strip
        strip_rect = pygame.Rect(CALC_X + 3, CALC_Y + 3, CALC_W - 6, 20)
        pygame.draw.rect(surface, (60, 60, 100), strip_rect, border_radius=18)

        # Brand label
        brand = font_tiny.render("STICK-CALC 3000", True, (150, 150, 200))
        surface.blit(brand, (CALC_X + CALC_W//2 - brand.get_width()//2, CALC_Y + 6))

        # Display screen
        display_rect = pygame.Rect(DISPLAY_X, DISPLAY_Y, DISPLAY_W, DISPLAY_H)
        # Screen glow effect
        if self.flash_timer > 0:
            glow_surf = pygame.Surface((DISPLAY_W + 10, DISPLAY_H + 10), pygame.SRCALPHA)
            glow_alpha = int(100 * (self.flash_timer / 10))
            pygame.draw.rect(glow_surf, (0, 255, 80, glow_alpha),
                           (0, 0, DISPLAY_W + 10, DISPLAY_H + 10), border_radius=12)
            surface.blit(glow_surf, (DISPLAY_X - 5, DISPLAY_Y - 5))

        pygame.draw.rect(surface, DISPLAY_BG, display_rect, border_radius=8)
        pygame.draw.rect(surface, (0, 100, 0), display_rect, 2, border_radius=8)

        # Screen scanlines
        for sy in range(DISPLAY_Y + 5, DISPLAY_Y + DISPLAY_H - 5, 4):
            pygame.draw.line(surface, (0, 30, 0),
                           (DISPLAY_X + 5, sy), (DISPLAY_X + DISPLAY_W - 5, sy), 1)

        # Display text
        disp_text = font_large.render(self.display_value, True, DISPLAY_TEXT)
        tx = DISPLAY_X + DISPLAY_W - disp_text.get_width() - 10
        ty = DISPLAY_Y + DISPLAY_H//2 - disp_text.get_height()//2
        surface.blit(disp_text, (tx, ty))

        # Small label
        label = font_tiny.render("RESULT", True, (0, 150, 0))
        surface.blit(label, (DISPLAY_X + 5, DISPLAY_Y + 5))

        # Arena separator
        arena_rect = pygame.Rect(ARENA_X, ARENA_Y - 10, ARENA_W, ARENA_H + 10)
        pygame.draw.rect(surface, (30, 30, 50), arena_rect, border_radius=10)
        pygame.draw.rect(surface, (60, 60, 100), arena_rect, 2, border_radius=10)

        # Arena label
        arena_label = font_tiny.render("~ THE CALCULATOR WORLD ~", True, (100, 100, 150))
        surface.blit(arena_label, (ARENA_X + ARENA_W//2 - arena_label.get_width()//2,
                                   ARENA_Y - 7))

        # Draw floor in arena
        for fx in range(ARENA_X + 5, ARENA_X + ARENA_W - 5, 20):
            pygame.draw.line(surface, (40, 40, 70),
                           (fx, ARENA_Y + ARENA_H - 5),
                           (fx + 10, ARENA_Y + ARENA_H - 5), 1)

        # Draw buttons
        for label, rect in button_rects.items():
            is_pressed = label in self.press_anim
            timer = self.press_anim.get(label, 0)

            if is_pressed:
                offset = min(5, int(5 * (timer / 20)))
                btn_rect = pygame.Rect(rect.x, rect.y + offset, rect.w, rect.h - offset)
                btn_color = BUTTON_PRESSED
                shadow_rect = pygame.Rect(rect.x + 3, rect.y + offset + 4, rect.w, rect.h - offset)
            else:
                btn_rect = rect
                btn_color = BUTTON_COLOR
                shadow_rect = pygame.Rect(rect.x + 3, rect.y + 4, rect.w, rect.h)

            # Button shadow
            pygame.draw.rect(surface, (30, 30, 60), shadow_rect, border_radius=8)
            # Button face
            pygame.draw.rect(surface, btn_color, btn_rect, border_radius=8)
            # Button highlight
            highlight_rect = pygame.Rect(btn_rect.x + 3, btn_rect.y + 3, btn_rect.w - 6, 10)
            pygame.draw.rect(surface, (min(btn_color[0]+50, 255),
                                       min(btn_color[1]+50, 255),
                                       min(btn_color[2]+50, 255)),
                           highlight_rect, border_radius=5)
            # Button border
            pygame.draw.rect(surface, (120, 120, 180), btn_rect, 2, border_radius=8)

            # Button label
            text_color = BLACK if is_pressed else WHITE
            btn_text = font_medium.render(label, True, text_color)
            bx = btn_rect.x + btn_rect.w // 2 - btn_text.get_width() // 2
            by = btn_rect.y + btn_rect.h // 2 - btn_text.get_height() // 2
            surface.blit(btn_text, (bx, by))

# Speech bubble class
class SpeechBubble:
    def __init__(self):
        self.text = ""
        self.timer = 0
        self.x = 0
        self.y = 0

    def show(self, text, x, y):
        self.text = text
        self.timer = 90
        self.x = x
        self.y = y

    def update(self):
        if self.timer > 0:
            self.timer -= 1

    def draw(self, surface):
        if self.timer <= 0:
            return
        alpha = min(255, self.timer * 5)
        text_surf = font_small.render(self.text, True, BLACK)
        bw = text_surf.get_width() + 16
        bh = text_surf.get_height() + 10
        bx = self.x - bw // 2
        by = self.y - bh - 20

        # Keep in bounds
        bx = max(CALC_X + 5, min(bx, CALC_X + CALC_W - bw - 5))

        bubble_surf = pygame.Surface((bw, bh + 10), pygame.SRCALPHA)
        pygame.draw.rect(bubble_surf, (255, 255, 255, alpha), (0, 0, bw, bh), border_radius=8)
        pygame.draw.rect(bubble_surf, (0, 0, 0, alpha), (0, 0, bw, bh), 2, border_radius=8)
        # Tail
        points = [(bw//2 - 6, bh), (bw//2 + 6, bh), (bw//2, bh + 10)]
        pygame.draw.polygon(bubble_surf, (255, 255, 255, alpha), points)
        pygame.draw.lines(bubble_surf, (0, 0, 0, alpha), False,
                         [(bw//2 - 6, bh), (bw//2, bh + 10), (bw//2 + 6, bh)], 2)
        bubble_surf.blit(text_surf, (8, 5))
        surface.blit(bubble_surf, (bx, by))

# Sayings for when buttons are pressed
DIGIT_SAYINGS = {
    '0': "Zero! Easy!",
    '1': "Number 1! That's me!",
    '2': "Two! Cool!",
    '3': "Three's a charm!",
    '4': "Four score!",
    '5': "High five!",
    '6': "Six-sational!",
    '7': "Lucky seven!",
    '8': "Eight is great!",
    '9': "Nine lives!",
}

# Main game
def main():
    stick = StickFigure()
    calc = Calculator()
    bubble = SpeechBubble()
    particles = []

    # Queue of keys to process (for rapid presses)
    key_queue = []
    currently_processing = False

    # Instructions
    instructions = [
        "Press 0-9 keys to make the",
        "stick figure press buttons!",
    ]

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
                    sys.exit()

                # Number keys
                for k in range(10):
                    if event.key == getattr(pygame, f'K_{k}') or \
                       event.key == getattr(pygame, f'K_KP{k}', -1):
                        digit = str(k)
                        key_queue.append(digit)

                if event.key == pygame.K_c or event.key == pygame.K_DELETE:
                    calc.display_value = "0"
                    bubble.show("Cleared!", int(stick.x), int(stick.y - 60))
                    # Spawn particles at stick figure position
                    for _ in range(20):
                        particles.append(Particle(int(stick.x), int(stick.y),
                                                (255, 100, 100)))

        # Process key queue - send stick figure to next button
        if key_queue and not stick.moving and not stick.pressing:
            digit = key_queue.pop(0)
            if digit in button_positions:
                tx, ty = button_positions[digit]
                stick.set_target(tx, ty, digit)
                currently_processing = True

        # Update
        stick.update()
        calc.update()
        bubble.update()

        # Check if stick figure just finished pressing
        if currently_processing and not stick.moving and not stick.pressing and stick.press_key:
            # This means pressing just ended - but we detect this differently
            pass

        # Check press completion
        if stick.pressing and stick.press_timer == 25:  # Just started pressing
            digit = stick.press_key
            calc.press(digit)
            # Speech bubble
            saying = DIGIT_SAYINGS.get(digit, f"Got {digit}!")
            bubble.show(saying, int(stick.x), int(stick.y - 50))
            # Particles
            if digit in button_positions:
                bx, by = button_positions[digit]
                for _ in range(25):
                    import random
                    color = random.choice([YELLOW, ORANGE, WHITE, GREEN, (100, 200, 255)])
                    particles.append(Particle(bx, by, color))

        # Update particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # Draw everything
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill((20, 20, 35))

        # Background stars
        import random
        # Static stars (use seed)
        rand = random.Random(42)
        for _ in range(50):
            sx = rand.randint(0, WIDTH)
            sy = rand.randint(0, HEIGHT)
            brightness = rand.randint(100, 255)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, sy), 1)

        # Draw calculator
        calc.draw(surface)

        # Draw stick figure (inside the arena)
        stick.draw(surface)

        # Draw particles
        for p in particles:
            p.draw(surface)

        # Draw speech bubble
        bubble.draw(surface)

        # Instructions panel
        inst_y = CALC_Y + CALC_H + 5
        for i, line in enumerate(instructions):
            inst_surf = font_tiny.render(line, True, (150, 150, 180))
            surface.blit(inst_surf, (WIDTH//2 - inst_surf.get_width()//2,
                                    inst_y + i * 18))

        # Clear hint
        clear_hint = font_tiny.render("Press C or DEL to clear", True, (120, 100, 100))
        surface.blit(clear_hint, (WIDTH//2 - clear_hint.get_width()//2, inst_y + 40))

        # FPS display (optional)
        fps_text = font_tiny.render(f"FPS: {int(clock.get_fps())}", True, (60, 60, 80))
        surface.blit(fps_text, (5, 5))

        screen.blit(surface, (0, 0))
        pygame.display.flip()

if __name__ == "__main__":
    main()