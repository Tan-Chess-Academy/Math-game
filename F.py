import pygame
import sys
import math
import random

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 550, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stick Figure Calculator Engineer")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 200, 50)
BLUE = (50, 100, 200)
RED = (200, 50, 50)
YELLOW = (255, 220, 0)
ORANGE = (255, 140, 0)
SKIN = (255, 200, 150)
DISPLAY_BG = (15, 30, 15)
DISPLAY_TEXT = (0, 255, 80)
CALC_BG = (40, 40, 60)
CALC_BORDER = (80, 80, 120)
BUTTON_COLOR = (70, 70, 120)
BUTTON_PRESSED = (255, 200, 0)
TOOL_COLOR = (160, 160, 180)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Fonts
font_large = pygame.font.SysFont("monospace", 52, bold=True)  # For digits
font_medium = pygame.font.SysFont("monospace", 28, bold=True)
font_small = pygame.font.SysFont("monospace", 18)
font_tiny = pygame.font.SysFont("monospace", 14)

# Calculator layout
CALC_X = 50
CALC_Y = 20
CALC_W = 450
CALC_H = 710

# Display area (stick figure's world)
DISPLAY_X = CALC_X + 20
DISPLAY_Y = CALC_Y + 30
DISPLAY_W = CALC_W - 40
DISPLAY_H = 120

# Button grid
BTN_W = 80
BTN_H = 60
BTN_MARGIN = 10
BTN_START_X = CALC_X + 40
BTN_START_Y = CALC_Y + 180

button_labels = [
    ['7', '8', '9', '/'],
    ['4', '5', '6', '*'],
    ['1', '2', '3', '-'],
    ['C', '0', '=', '+'],
]

button_rects = {}
button_positions = {}

for row_i, row in enumerate(button_labels):
    for col_i, label in enumerate(row):
        bx = BTN_START_X + col_i * (BTN_W + BTN_MARGIN)
        by = BTN_START_Y + row_i * (BTN_H + BTN_MARGIN)
        rect = pygame.Rect(bx, by, BTN_W, BTN_H)
        button_rects[label] = rect
        button_positions[label] = (bx + BTN_W // 2, by + BTN_H // 2)

# ===== DIGIT TILE (the numbers the stick figure manipulates) =====
class DigitTile:
    def __init__(self, char, index):
        self.char = char
        self.index = index
        self.x = DISPLAY_X + DISPLAY_W - 50 - index * 35
        self.y = DISPLAY_Y + DISPLAY_H // 2
        self.target_y = self.y
        self.flipping = False
        self.flip_timer = 0
        self.new_char = char

    def set_char(self, new_char):
        if new_char != self.char:
            self.new_char = new_char
            self.flipping = True
            self.flip_timer = 20

    def update(self):
        if self.flipping:
            self.flip_timer -= 1
            # Flip animation (move up and down)
            t = self.flip_timer / 20
            self.y = self.target_y - math.sin(t * math.pi) * 15
            if self.flip_timer <= 0:
                self.char = self.new_char
                self.flipping = False
                self.y = self.target_y

    def draw(self, surface):
        # Draw tile background
        tile_rect = pygame.Rect(self.x - 15, self.y - 25, 30, 50)
        pygame.draw.rect(surface, (0, 60, 0), tile_rect, border_radius=4)
        pygame.draw.rect(surface, (0, 100, 0), tile_rect, 2, border_radius=4)
        
        # Draw digit
        if not self.flipping or self.flip_timer % 4 < 2:
            text = font_large.render(self.char, True, DISPLAY_TEXT)
        else:
            text = font_large.render(self.new_char, True, DISPLAY_TEXT)
        
        surface.blit(text, (self.x - text.get_width()//2, self.y - text.get_height()//2))

# ===== STICK FIGURE ENGINEER (lives in the display) =====
class StickFigureEngineer:
    def __init__(self):
        self.x = DISPLAY_X + DISPLAY_W // 2
        self.y = DISPLAY_Y + DISPLAY_H - 30
        self.target_x = self.x
        self.target_y = self.y
        self.speed = 4
        self.moving = False
        self.working = False
        self.work_timer = 0
        self.work_type = None  # 'flip', 'slide', 'calculate'
        self.target_tile = None
        self.walk_anim = 0
        self.direction = 1
        self.idle_anim = 0
        self.tool = None  # 'wrench', 'hammer', 'calculator'
        self.head_radius = 12
        self.body_len = 25
        self.arm_len = 18
        self.leg_len = 22
        self.expression = "normal"
        self.blink_timer = 0
        self.blink = False
        self.sweat_drops = []

    def set_task(self, task_type, target_x, target_tile=None):
        self.work_type = task_type
        self.target_x = target_x
        self.target_y = DISPLAY_Y + DISPLAY_H - 30
        self.target_tile = target_tile
        self.moving = True
        
        if task_type == 'flip':
            self.tool = 'hammer'
            self.expression = "focused"
        elif task_type == 'calculate':
            self.tool = 'calculator'
            self.expression = "thinking"

    def update(self):
        self.idle_anim += 0.08
        self.blink_timer += 1
        if self.blink_timer > 100:
            self.blink = True
            if self.blink_timer > 105:
                self.blink = False
                self.blink_timer = 0

        if self.moving:
            dx = self.target_x - self.x
            if abs(dx) < self.speed:
                self.x = self.target_x
                self.moving = False
                self.working = True
                self.work_timer = 30
                self.walk_anim = 0
            else:
                self.x += self.speed if dx > 0 else -self.speed
                self.walk_anim += 0.3
                self.direction = 1 if dx > 0 else -1

        if self.working:
            self.work_timer -= 1
            # Add sweat when working hard
            if self.work_timer % 8 == 0 and self.work_type == 'calculate':
                self.sweat_drops.append([self.x + 8, self.y - 15, 15])
            
            if self.work_timer <= 0:
                self.working = False
                self.tool = None
                self.expression = "happy"
                self.target_tile = None

        # Update sweat drops
        for drop in self.sweat_drops[:]:
            drop[1] += 2
            drop[2] -= 1
            if drop[2] <= 0:
                self.sweat_drops.remove(drop)

    def draw(self, surface):
        x = int(self.x)
        y = int(self.y + math.sin(self.idle_anim) * 2)

        hr = self.head_radius
        bl = self.body_len
        al = self.arm_len
        ll = self.leg_len

        head_y = y
        body_top = y + hr
        body_bot = y + hr + bl

        # Walking animation
        if self.moving:
            leg_angle_l = math.sin(self.walk_anim) * 0.5
            leg_angle_r = -math.sin(self.walk_anim) * 0.5
            arm_angle_l = -math.sin(self.walk_anim) * 0.4
            arm_angle_r = math.sin(self.walk_anim) * 0.4
        elif self.working:
            leg_angle_l = 0.1
            leg_angle_r = -0.1
            arm_angle_l = -1.0
            arm_angle_r = -0.3
        else:
            leg_angle_l = math.sin(self.idle_anim) * 0.1
            leg_angle_r = -math.sin(self.idle_anim) * 0.1
            arm_angle_l = math.sin(self.idle_anim * 0.8) * 0.2
            arm_angle_r = -math.sin(self.idle_anim * 0.8) * 0.2

        # Shadow
        pygame.draw.ellipse(surface, (0, 0, 0, 80), (x - 15, body_bot + ll - 5, 30, 10))

        # Draw legs
        lx1, lx2 = x - 7, x + 7
        lleg_end = (lx1 + math.sin(leg_angle_l) * ll * self.direction,
                   body_bot + math.cos(leg_angle_l) * ll)
        rleg_end = (lx2 + math.sin(leg_angle_r) * ll * self.direction,
                   body_bot + math.cos(leg_angle_r) * ll)
        pygame.draw.line(surface, BLACK, (lx1, body_bot), lleg_end, 3)
        pygame.draw.line(surface, BLACK, (lx2, body_bot), rleg_end, 3)

        # Draw body
        pygame.draw.line(surface, BLACK, (x, body_top), (x, body_bot), 3)

        # Draw arms
        larm_end = (x + math.sin(arm_angle_l) * al * self.direction,
                   body_top + 8 + math.cos(arm_angle_l) * al)
        rarm_end = (x + math.sin(arm_angle_r) * al * self.direction,
                   body_top + 8 + math.cos(arm_angle_r) * al)
        pygame.draw.line(surface, BLACK, (x, body_top + 8), larm_end, 3)
        
        # Right arm holds tool
        pygame.draw.line(surface, BLACK, (x, body_top + 8), rarm_end, 3)
        
        # Draw tool
        if self.tool == 'hammer' and self.working:
            hammer_x, hammer_y = int(rarm_end[0]), int(rarm_end[1])
            pygame.draw.rect(surface, (100, 60, 30), (hammer_x, hammer_y - 8, 12, 16), border_radius=2)
            pygame.draw.rect(surface, TOOL_COLOR, (hammer_x + 4, hammer_y - 20, 4, 12))
        elif self.tool == 'calculator' and self.working:
            calc_x, calc_y = int(rarm_end[0]), int(rarm_end[1])
            pygame.draw.rect(surface, (50, 50, 70), (calc_x, calc_y - 10, 16, 20), border_radius=3)
            pygame.draw.rect(surface, (0, 200, 0), (calc_x + 2, calc_y - 8, 12, 6))

        # Draw head
        pygame.draw.circle(surface, SKIN, (x, head_y), hr)
        pygame.draw.circle(surface, BLACK, (x, head_y), hr, 2)

        # Hard hat
        pygame.draw.arc(surface, YELLOW, (x - hr - 2, head_y - hr - 5, hr*2 + 4, hr*2), 
                       math.pi * 0.1, math.pi * 0.9, 8)
        pygame.draw.rect(surface, YELLOW, (x - hr - 2, head_y - hr + 6, hr*2 + 4, 6), border_radius=2)

        # Eyes
        offset = 4
        if self.blink:
            pygame.draw.line(surface, BLACK, (x - offset - 2, head_y - 2),
                           (x - offset + 2, head_y - 2), 2)
            pygame.draw.line(surface, BLACK, (x + offset - 2, head_y - 2),
                           (x + offset + 2, head_y - 2), 2)
        else:
            pygame.draw.circle(surface, BLACK, (x - offset, head_y - 2), 2)
            pygame.draw.circle(surface, BLACK, (x + offset, head_y - 2), 2)

        # Mouth
        if self.expression == "happy":
            pygame.draw.arc(surface, BLACK, (x - 6, head_y + 2, 12, 7), math.pi, 2*math.pi, 2)
        elif self.expression == "focused":
            pygame.draw.line(surface, BLACK, (x - 4, head_y + 4), (x + 4, head_y + 4), 2)
        elif self.expression == "thinking":
            pygame.draw.circle(surface, BLACK, (x, head_y + 4), 3)
            pygame.draw.circle(surface, RED, (x, head_y + 5), 2)

        # Overalls
        pygame.draw.rect(surface, BLUE, (x - 7, body_top + 2, 14, bl - 2), border_radius=3)
        pygame.draw.rect(surface, (30, 30, 100), (x - 7, body_top + 2, 14, 8))

        # Sweat drops
        for drop in self.sweat_drops:
            pygame.draw.circle(surface, (100, 150, 255), (int(drop[0]), int(drop[1])), 2)

# ===== CALCULATOR ENGINE =====
class CalculatorEngine:
    def __init__(self):
        self.current_value = "0"
        self.stored_value = None
        self.operation = None
        self.reset_next = False
        self.tiles = [DigitTile('0', 0)]
        self.engineer = StickFigureEngineer()
        self.pressed_button = None
        self.press_anim = {}
        self.task_queue = []
        self.processing_task = False

    def add_digit(self, digit):
        if self.reset_next:
            self.current_value = digit
            self.reset_next = False
        elif self.current_value == "0":
            self.current_value = digit
        elif len(self.current_value) < 10:
            self.current_value += digit
        
        self.update_tiles()

    def set_operation(self, op):
        if self.stored_value is None:
            self.stored_value = float(self.current_value)
        elif self.operation and not self.reset_next:
            self.calculate()
        
        self.operation = op
        self.reset_next = True

    def calculate(self):
        if self.stored_value is None or self.operation is None:
            return
        
        # Engineer does the calculation work
        self.task_queue.append(('calculate', self.stored_value, self.operation, float(self.current_value)))
        self.processing_task = True

    def clear(self):
        self.current_value = "0"
        self.stored_value = None
        self.operation = None
        self.reset_next = False
        self.update_tiles()

    def update_tiles(self):
        # Update digit tiles to match current value
        new_tiles = []
        for i, char in enumerate(reversed(self.current_value)):
            if i < len(self.tiles):
                # Existing tile - engineer needs to flip it
                if self.tiles[i].char != char:
                    self.task_queue.append(('flip', i, char))
            else:
                # New tile needed - engineer needs to slide it in
                new_tiles.append(DigitTile(char, i))
        
        # Add new tiles
        self.tiles.extend(new_tiles)
        
        # Remove extra tiles
        if len(self.tiles) > len(self.current_value):
            self.tiles = self.tiles[:len(self.current_value)]
        
        # Reindex
        for i, tile in enumerate(self.tiles):
            tile.index = i
            tile.x = DISPLAY_X + DISPLAY_W - 50 - i * 35

    def process_tasks(self):
        if self.task_queue and not self.engineer.moving and not self.engineer.working:
            task = self.task_queue.pop(0)
            
            if task[0] == 'flip':
                tile_index, new_char = task[1], task[2]
                if tile_index < len(self.tiles):
                    tile = self.tiles[tile_index]
                    self.engineer.set_task('flip', tile.x, tile)
                    tile.set_char(new_char)
            
            elif task[0] == 'calculate':
                _, val1, op, val2 = task
                # Engineer runs to center to calculate
                self.engineer.set_task('calculate', DISPLAY_X + DISPLAY_W // 2)
                
                # Do the math
                try:
                    if op == '+':
                        result = val1 + val2
                    elif op == '-':
                        result = val1 - val2
                    elif op == '*':
                        result = val1 * val2
                    elif op == '/':
                        result = val1 / val2 if val2 != 0 else float('inf')
                    
                    # Format result
                    if result == float('inf'):
                        result_str = "ERROR"
                    elif result == int(result):
                        result_str = str(int(result))
                    else:
                        result_str = f"{result:.8g}"
                    
                    self.current_value = result_str
                    self.stored_value = result
                    self.reset_next = True
                    self.update_tiles()
                    
                except:
                    self.current_value = "ERROR"
                    self.update_tiles()
                
                self.operation = None

        self.engineer.update()
        for tile in self.tiles:
            tile.update()

    def draw(self, surface):
        # Calculator body
        body_rect = pygame.Rect(CALC_X, CALC_Y, CALC_W, CALC_H)
        pygame.draw.rect(surface, CALC_BG, body_rect, border_radius=20)
        pygame.draw.rect(surface, CALC_BORDER, body_rect, 3, border_radius=20)

        # Brand
        brand = font_medium.render("ENGINEER CALC", True, (150, 150, 200))
        surface.blit(brand, (CALC_X + CALC_W//2 - brand.get_width()//2, CALC_Y + 8))

        # Display screen
        display_rect = pygame.Rect(DISPLAY_X, DISPLAY_Y, DISPLAY_W, DISPLAY_H)
        pygame.draw.rect(surface, DISPLAY_BG, display_rect, border_radius=10)
        pygame.draw.rect(surface, (0, 80, 0), display_rect, 3, border_radius=10)

        # Scanlines
        for sy in range(DISPLAY_Y + 5, DISPLAY_Y + DISPLAY_H - 5, 4):
            pygame.draw.line(surface, (0, 25, 0),
                           (DISPLAY_X + 5, sy), (DISPLAY_X + DISPLAY_W - 5, sy), 1)

        # Draw digit tiles
        for tile in self.tiles:
            tile.draw(surface)

        # Draw engineer (inside display)
        self.engineer.draw(surface)

        # Operation indicator
        if self.operation:
            op_text = font_medium.render(self.operation, True, YELLOW)
            surface.blit(op_text, (DISPLAY_X + 10, DISPLAY_Y + 10))

        # Draw buttons
        for label, rect in button_rects.items():
            is_pressed = label in self.press_anim
            timer = self.press_anim.get(label, 0)

            btn_rect = rect
            if is_pressed:
                btn_rect = pygame.Rect(rect.x, rect.y + 4, rect.w, rect.h - 4)
                btn_color = BUTTON_PRESSED
            else:
                btn_color = BUTTON_COLOR

            pygame.draw.rect(surface, (30, 30, 60),
                           (rect.x + 3, rect.y + 4, rect.w, rect.h), border_radius=8)
            pygame.draw.rect(surface, btn_color, btn_rect, border_radius=8)
            pygame.draw.rect(surface, (120, 120, 180), btn_rect, 2, border_radius=8)

            text_color = BLACK if is_pressed else WHITE
            btn_text = font_medium.render(label, True, text_color)
            bx = btn_rect.x + btn_rect.w // 2 - btn_text.get_width() // 2
            by = btn_rect.y + btn_rect.h // 2 - btn_text.get_height() // 2
            surface.blit(btn_text, (bx, by))

    def press_animation(self, button):
        self.press_anim[button] = 15

    def update(self):
        for key in list(self.press_anim.keys()):
            self.press_anim[key] -= 1
            if self.press_anim[key] <= 0:
                del self.press_anim[key]
        
        self.process_tasks()

# ===== MAIN GAME =====
def main():
    calc = CalculatorEngine()

    instructions = [
        "0-9: Enter numbers",
        "+ - * / : Operations",
        "Enter/= : Calculate",
        "C/Del : Clear",
        "The engineer lives IN the screen!"
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

                # Numbers
                for k in range(10):
                    if event.key == getattr(pygame, f'K_{k}') or \
                       event.key == getattr(pygame, f'K_KP{k}', -1):
                        digit = str(k)
                        calc.add_digit(digit)
                        calc.press_animation(digit)

                # Operations
                if event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                    calc.set_operation('+')
                    calc.press_animation('+')
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    calc.set_operation('-')
                    calc.press_animation('-')
                elif event.key == pygame.K_ASTERISK or event.key == pygame.K_KP_MULTIPLY:
                    calc.set_operation('*')
                    calc.press_animation('*')
                elif event.key == pygame.K_SLASH or event.key == pygame.K_KP_DIVIDE:
                    calc.set_operation('/')
                    calc.press_animation('/')

                # Equals/Enter
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER or event.key == pygame.K_EQUALS:
                    calc.calculate()
                    calc.press_animation('=')

                # Clear
                if event.key == pygame.K_c or event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    calc.clear()
                    calc.press_animation('C')

        calc.update()

        # Draw
        screen.fill((25, 25, 40))

        # Background stars
        for i in range(60):
            sx = (i * 137) % WIDTH
            sy = (i * 211) % HEIGHT
            brightness = 100 + (i * 17) % 155
            pygame.draw.circle(screen, (brightness, brightness, brightness), (sx, sy), 1)

        calc.draw(screen)

        # Instructions
        inst_y = CALC_Y + CALC_H + 10
        for i, line in enumerate(instructions):
            inst_surf = font_tiny.render(line, True, (150, 150, 180))
            screen.blit(inst_surf, (WIDTH//2 - inst_surf.get_width()//2,
                                    inst_y + i * 16))

        pygame.display.flip()

if __name__ == "__main__":
    main()