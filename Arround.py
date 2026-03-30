import pygame
import sys
import math
import random

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stick Figure Calculator - Living Display")

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

# Display colors (LCD green style)
DISPLAY_BG = (15, 30, 15)
DISPLAY_TEXT = (0, 255, 80)
SEGMENT_ON = (0, 255, 80)
SEGMENT_OFF = (20, 50, 20)
SEGMENT_GLOW = (100, 255, 150, 100)

# Calculator colors
CALC_BG = (40, 40, 60)
CALC_BORDER = (80, 80, 120)
BUTTON_COLOR = (70, 70, 120)
BUTTON_HOVER = (100, 100, 180)
BUTTON_PRESSED = (255, 200, 0)
BUTTON_OP = (100, 70, 120)
BUTTON_EQUALS = (70, 150, 70)
BUTTON_CLEAR = (150, 70, 70)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Fonts
font_large = pygame.font.SysFont("monospace", 36, bold=True)
font_medium = pygame.font.SysFont("monospace", 24, bold=True)
font_small = pygame.font.SysFont("monospace", 16)
font_tiny = pygame.font.SysFont("monospace", 12)

# Calculator layout
CALC_X = 50
CALC_Y = 20
CALC_W = 500
CALC_H = 710

# Display area (where stick figure lives!)
DISPLAY_X = CALC_X + 20
DISPLAY_Y = CALC_Y + 40
DISPLAY_W = CALC_W - 40
DISPLAY_H = 180

# Seven-segment display configuration
SEGMENT_WIDTH = 8
SEGMENT_LENGTH = 30
DIGIT_WIDTH = 50
DIGIT_HEIGHT = 70
DIGIT_SPACING = 58
NUM_DIGITS = 8
DIGITS_START_X = DISPLAY_X + 20
DIGITS_START_Y = DISPLAY_Y + 80

# Seven segment patterns (a,b,c,d,e,f,g)
SEGMENT_PATTERNS = {
    '0': (1,1,1,1,1,1,0),
    '1': (0,1,1,0,0,0,0),
    '2': (1,1,0,1,1,0,1),
    '3': (1,1,1,1,0,0,1),
    '4': (0,1,1,0,0,1,1),
    '5': (1,0,1,1,0,1,1),
    '6': (1,0,1,1,1,1,1),
    '7': (1,1,1,0,0,0,0),
    '8': (1,1,1,1,1,1,1),
    '9': (1,1,1,1,0,1,1),
    '-': (0,0,0,0,0,0,1),
    ' ': (0,0,0,0,0,0,0),
    'E': (1,0,0,1,1,1,1),
    'r': (0,0,0,0,1,0,1),
}

# Segment positions relative to digit origin (for drawing and for stick figure to reach)
def get_segment_positions(dx, dy):
    """Returns dict of segment letter -> (x, y, is_horizontal)"""
    sw = SEGMENT_WIDTH
    sl = SEGMENT_LENGTH
    return {
        'a': (dx + sw//2, dy, True),                          # top horizontal
        'b': (dx + sl, dy + sw//2, False),                    # top-right vertical
        'c': (dx + sl, dy + sl + sw, False),                  # bottom-right vertical
        'd': (dx + sw//2, dy + 2*sl + sw, True),              # bottom horizontal
        'e': (dx, dy + sl + sw, False),                       # bottom-left vertical
        'f': (dx, dy + sw//2, False),                         # top-left vertical
        'g': (dx + sw//2, dy + sl + sw//2, True),             # middle horizontal
    }

# Button grid
BUTTONS = []
button_labels = [
    ['C', '±', '%', '÷'],
    ['7', '8', '9', '×'],
    ['4', '5', '6', '-'],
    ['1', '2', '3', '+'],
    ['0', '0', '.', '='],  # 0 spans two columns
]

BTN_W = 100
BTN_H = 55
BTN_MARGIN = 10
BTN_START_X = CALC_X + 30
BTN_START_Y = DISPLAY_Y + DISPLAY_H + 40

button_rects = {}
button_positions = {}

# Create button rectangles
for row_i, row in enumerate(button_labels):
    col_offset = 0
    for col_i, label in enumerate(row):
        if row_i == 4 and col_i == 1:  # Skip second '0' (it's a span indicator)
            continue
        
        bx = BTN_START_X + col_offset * (BTN_W + BTN_MARGIN)
        by = BTN_START_Y + row_i * (BTN_H + BTN_MARGIN)
        
        # Make '0' button wider
        if row_i == 4 and col_i == 0:
            rect = pygame.Rect(bx, by, BTN_W * 2 + BTN_MARGIN, BTN_H)
            col_offset += 2
        else:
            rect = pygame.Rect(bx, by, BTN_W, BTN_H)
            col_offset += 1
        
        if label not in button_rects:  # Don't overwrite
            button_rects[label] = rect
            button_positions[label] = (rect.centerx, rect.centery)

# Key mappings
KEY_MAP = {
    pygame.K_0: '0', pygame.K_KP0: '0',
    pygame.K_1: '1', pygame.K_KP1: '1',
    pygame.K_2: '2', pygame.K_KP2: '2',
    pygame.K_3: '3', pygame.K_KP3: '3',
    pygame.K_4: '4', pygame.K_KP4: '4',
    pygame.K_5: '5', pygame.K_KP5: '5',
    pygame.K_6: '6', pygame.K_KP6: '6',
    pygame.K_7: '7', pygame.K_KP7: '7',
    pygame.K_8: '8', pygame.K_KP8: '8',
    pygame.K_9: '9', pygame.K_KP9: '9',
    pygame.K_PLUS: '+', pygame.K_KP_PLUS: '+',
    pygame.K_MINUS: '-', pygame.K_KP_MINUS: '-',
    pygame.K_ASTERISK: '×', pygame.K_KP_MULTIPLY: '×',
    pygame.K_SLASH: '÷', pygame.K_KP_DIVIDE: '÷',
    pygame.K_RETURN: '=', pygame.K_KP_ENTER: '=',
    pygame.K_EQUALS: '=',
    pygame.K_PERIOD: '.', pygame.K_KP_PERIOD: '.',
    pygame.K_c: 'C', pygame.K_DELETE: 'C', pygame.K_BACKSPACE: 'C',
    pygame.K_PERCENT: '%',
}

# Particle class
class Particle:
    def __init__(self, x, y, color, size=None, velocity=None):
        self.x = x
        self.y = y
        if velocity:
            self.vx, self.vy = velocity
        else:
            self.vx = random.uniform(-3, 3)
            self.vy = random.uniform(-5, -1)
        self.color = color
        self.life = random.randint(20, 40)
        self.max_life = self.life
        self.radius = size if size else random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        r = max(1, int(self.radius * (self.life / self.max_life)))
        surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        color = (*self.color[:3], alpha) if len(self.color) == 3 else (*self.color[:3], min(alpha, self.color[3]))
        pygame.draw.circle(surf, color, (r, r), r)
        surface.blit(surf, (int(self.x) - r, int(self.y) - r))

# Spark effect for segment changes
class Spark:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(10, 25)
        self.max_life = self.life
        self.color = random.choice([SEGMENT_ON, YELLOW, WHITE, (150, 255, 150)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(3 * (self.life / self.max_life)))
        surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (size, size), size)
        surface.blit(surf, (int(self.x) - size, int(self.y) - size))

# Tool class (wrench, hammer, etc.)
class Tool:
    def __init__(self, tool_type):
        self.type = tool_type  # 'wrench', 'hammer', 'screwdriver'
        self.angle = 0
        self.using = False
        self.use_timer = 0

    def start_use(self):
        self.using = True
        self.use_timer = 20

    def update(self):
        if self.using:
            self.use_timer -= 1
            self.angle = math.sin(self.use_timer * 0.5) * 0.8
            if self.use_timer <= 0:
                self.using = False
                self.angle = 0

    def draw(self, surface, x, y, direction):
        if self.type == 'wrench':
            # Draw wrench
            end_x = x + math.cos(self.angle + 0.5 * direction) * 20
            end_y = y + math.sin(self.angle + 0.5) * 20
            pygame.draw.line(surface, (150, 150, 150), (x, y), (int(end_x), int(end_y)), 3)
            pygame.draw.circle(surface, (150, 150, 150), (int(end_x), int(end_y)), 5)
            pygame.draw.circle(surface, (100, 100, 100), (int(end_x), int(end_y)), 3)

# Stick figure that lives in the display
class DisplayStickFigure:
    def __init__(self):
        # Start in center of display
        self.x = DISPLAY_X + DISPLAY_W // 2
        self.y = DISPLAY_Y + DISPLAY_H - 40
        self.target_x = self.x
        self.target_y = self.y
        self.speed = 4
        self.moving = False
        self.working = False
        self.work_timer = 0
        self.work_segment = None
        self.work_digit_idx = None
        self.work_turning_on = True
        
        # Animation
        self.walk_anim = 0
        self.idle_anim = 0
        self.direction = 1
        self.bounce = 0
        self.blink_timer = 0
        self.blink = False
        self.expression = "happy"
        
        # Tool
        self.tool = Tool('wrench')
        self.carrying_segment = False
        
        # Dimensions
        self.head_radius = 10
        self.body_len = 20
        self.arm_len = 15
        self.leg_len = 18
        
        # Trail
        self.trail = []
        
        # Task queue
        self.task_queue = []  # List of (digit_idx, segment, turn_on)
        
        # Speech
        self.speech = ""
        self.speech_timer = 0
        
        # Ladder for reaching top segments
        self.on_ladder = False
        self.ladder_x = 0

    def add_task(self, digit_idx, segment, turn_on):
        self.task_queue.append((digit_idx, segment, turn_on))

    def say(self, text):
        self.speech = text
        self.speech_timer = 90

    def get_segment_world_pos(self, digit_idx, segment):
        """Get world position of a segment"""
        dx = DIGITS_START_X + digit_idx * DIGIT_SPACING
        dy = DIGITS_START_Y
        positions = get_segment_positions(dx, dy)
        if segment in positions:
            sx, sy, is_horiz = positions[segment]
            if is_horiz:
                return (sx + SEGMENT_LENGTH // 2, sy)
            else:
                return (sx, sy + SEGMENT_LENGTH // 2)
        return (dx, dy)

    def update(self, display_digits, current_digit_states):
        self.idle_anim += 0.08
        self.blink_timer += 1
        if self.blink_timer > 100:
            self.blink = True
            if self.blink_timer > 105:
                self.blink = False
                self.blink_timer = 0

        self.tool.update()
        
        if self.speech_timer > 0:
            self.speech_timer -= 1

        # Process task queue
        if not self.moving and not self.working and self.task_queue:
            digit_idx, segment, turn_on = self.task_queue.pop(0)
            target_pos = self.get_segment_world_pos(digit_idx, segment)
            self.target_x = target_pos[0]
            # Adjust y based on segment position
            seg_y = target_pos[1]
            self.target_y = seg_y + 15  # Stand below the segment
            self.moving = True
            self.work_segment = segment
            self.work_digit_idx = digit_idx
            self.work_turning_on = turn_on
            self.expression = "working"
            
            # Check if we need ladder (top segments)
            if segment in ['a', 'b', 'f']:
                self.on_ladder = True
                self.ladder_x = target_pos[0]

        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx*dx + dy*dy)

            # Trail
            if len(self.trail) < 6:
                self.trail.append((self.x, self.y))
            else:
                self.trail.pop(0)
                self.trail.append((self.x, self.y))

            if dist < self.speed:
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
                self.working = True
                self.work_timer = 30
                self.walk_anim = 0
                self.tool.start_use()
                self.trail = []
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
                self.walk_anim += 0.25
                self.direction = 1 if dx > 0 else -1

        if self.working:
            self.work_timer -= 1
            if self.work_timer == 15:
                # Actually change the segment
                if self.work_digit_idx is not None and self.work_segment:
                    return (self.work_digit_idx, self.work_segment, self.work_turning_on)
            if self.work_timer <= 0:
                self.working = False
                self.expression = "happy"
                self.on_ladder = False
                self.work_segment = None
                self.work_digit_idx = None

        # Idle bounce
        if not self.moving and not self.working:
            self.bounce = math.sin(self.idle_anim) * 2
            
        return None

    def draw(self, surface):
        x = int(self.x)
        y = int(self.y + self.bounce)

        # Draw trail (glowing)
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(150 * (i / len(self.trail)))
            radius = max(2, int(4 * (i / len(self.trail))))
            glow_surf = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (0, 255, 80, alpha), (radius*2, radius*2), radius*2)
            pygame.draw.circle(glow_surf, (150, 255, 150, alpha), (radius*2, radius*2), radius)
            surface.blit(glow_surf, (int(tx) - radius*2, int(ty) - radius*2))

        # Draw ladder if on it
        if self.on_ladder:
            ladder_h = 50
            lx = int(self.ladder_x) - 10
            ly = int(self.y) - ladder_h + 10
            # Ladder sides
            pygame.draw.line(surface, (139, 90, 43), (lx, ly), (lx, int(self.y) + 10), 3)
            pygame.draw.line(surface, (139, 90, 43), (lx + 20, ly), (lx + 20, int(self.y) + 10), 3)
            # Rungs
            for ry in range(ly, int(self.y) + 5, 10):
                pygame.draw.line(surface, (160, 110, 60), (lx, ry), (lx + 20, ry), 2)

        hr = self.head_radius
        bl = self.body_len
        al = self.arm_len
        ll = self.leg_len

        head_y = y - ll - bl - hr
        body_top = y - ll - bl
        body_bot = y - ll

        # Animation angles
        if self.moving:
            leg_angle_l = math.sin(self.walk_anim) * 0.5
            leg_angle_r = -math.sin(self.walk_anim) * 0.5
            arm_angle_l = -math.sin(self.walk_anim) * 0.4
            arm_angle_r = math.sin(self.walk_anim) * 0.4
        elif self.working:
            t = self.work_timer / 30
            leg_angle_l = 0.1
            leg_angle_r = -0.1
            # Reaching up animation
            arm_angle_l = -1.2 + math.sin(self.work_timer * 0.5) * 0.3
            arm_angle_r = -1.5 + math.sin(self.work_timer * 0.5) * 0.3
        else:
            leg_angle_l = math.sin(self.idle_anim * 0.5) * 0.05
            leg_angle_r = -math.sin(self.idle_anim * 0.5) * 0.05
            arm_angle_l = math.sin(self.idle_anim * 0.7) * 0.15 - 0.2
            arm_angle_r = -math.sin(self.idle_anim * 0.7) * 0.15 + 0.2

        # Shadow
        shadow_w = 25 if not self.on_ladder else 15
        shadow_surf = pygame.Surface((shadow_w, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, shadow_w, 8))
        surface.blit(shadow_surf, (x - shadow_w//2, y - 3))

        # Legs with glow effect
        for leg_angle, lx_offset in [(leg_angle_l, -4), (leg_angle_r, 4)]:
            lx = x + lx_offset
            leg_end_x = lx + math.sin(leg_angle) * ll * self.direction
            leg_end_y = body_bot + math.cos(leg_angle) * ll
            # Glow
            pygame.draw.line(surface, (0, 200, 50), (lx, body_bot), 
                           (int(leg_end_x), int(leg_end_y)), 5)
            # Main line
            pygame.draw.line(surface, SEGMENT_ON, (lx, body_bot), 
                           (int(leg_end_x), int(leg_end_y)), 3)

        # Body with glow
        pygame.draw.line(surface, (0, 200, 50), (x, body_top), (x, body_bot), 5)
        pygame.draw.line(surface, SEGMENT_ON, (x, body_top), (x, body_bot), 3)

        # Arms
        for arm_angle, side in [(arm_angle_l, -1), (arm_angle_r, 1)]:
            arm_end_x = x + math.sin(arm_angle * side) * al
            arm_end_y = body_top + 8 + math.cos(arm_angle) * al * 0.6
            # Glow
            pygame.draw.line(surface, (0, 200, 50), (x, body_top + 6), 
                           (int(arm_end_x), int(arm_end_y)), 5)
            # Main
            pygame.draw.line(surface, SEGMENT_ON, (x, body_top + 6), 
                           (int(arm_end_x), int(arm_end_y)), 3)
            
            # Draw tool in right hand when working
            if self.working and side == self.direction:
                self.tool.draw(surface, int(arm_end_x), int(arm_end_y), self.direction)

        # Head glow
        pygame.draw.circle(surface, (0, 200, 50), (x, int(head_y)), hr + 3)
        # Head
        pygame.draw.circle(surface, SEGMENT_ON, (x, int(head_y)), hr)
        # Inner head darker
        pygame.draw.circle(surface, (0, 200, 50), (x, int(head_y)), hr - 2)

        # Eyes
        eye_y = int(head_y) - 1
        if self.blink:
            pygame.draw.line(surface, DISPLAY_BG, (x - 4, eye_y), (x - 1, eye_y), 2)
            pygame.draw.line(surface, DISPLAY_BG, (x + 1, eye_y), (x + 4, eye_y), 2)
        else:
            pygame.draw.circle(surface, DISPLAY_BG, (x - 3, eye_y), 2)
            pygame.draw.circle(surface, DISPLAY_BG, (x + 3, eye_y), 2)
            # Eye shine
            pygame.draw.circle(surface, WHITE, (x - 2, eye_y - 1), 1)
            pygame.draw.circle(surface, WHITE, (x + 4, eye_y - 1), 1)

        # Mouth
        mouth_y = int(head_y) + 4
        if self.expression == "happy":
            pygame.draw.arc(surface, DISPLAY_BG, (x - 4, mouth_y - 2, 8, 6), 
                          math.pi, 2*math.pi, 2)
        elif self.expression == "working":
            # Determined expression
            pygame.draw.line(surface, DISPLAY_BG, (x - 3, mouth_y), (x + 3, mouth_y), 2)
        
        # Hard hat when working
        if self.working or self.moving:
            hat_color = YELLOW
            pygame.draw.ellipse(surface, hat_color, 
                              (x - hr - 2, int(head_y) - hr - 2, hr*2 + 4, 8))
            pygame.draw.rect(surface, hat_color,
                           (x - hr + 2, int(head_y) - hr - 6, hr*2 - 4, 8))

        # Speech bubble
        if self.speech_timer > 0:
            self.draw_speech(surface, x, int(head_y) - hr - 20)

    def draw_speech(self, surface, x, y):
        alpha = min(255, self.speech_timer * 5)
        text_surf = font_tiny.render(self.speech, True, DISPLAY_BG)
        bw = text_surf.get_width() + 12
        bh = text_surf.get_height() + 8
        bx = x - bw // 2
        by = y - bh

        # Keep in display bounds
        bx = max(DISPLAY_X + 5, min(bx, DISPLAY_X + DISPLAY_W - bw - 5))
        by = max(DISPLAY_Y + 5, by)

        bubble_surf = pygame.Surface((bw, bh + 8), pygame.SRCALPHA)
        pygame.draw.rect(bubble_surf, (200, 255, 200, alpha), (0, 0, bw, bh), border_radius=5)
        pygame.draw.rect(bubble_surf, (0, 150, 0, alpha), (0, 0, bw, bh), 2, border_radius=5)
        # Tail
        pygame.draw.polygon(bubble_surf, (200, 255, 200, alpha), 
                          [(bw//2 - 4, bh), (bw//2 + 4, bh), (bw//2, bh + 6)])
        
        bubble_surf.blit(text_surf, (6, 4))
        surface.blit(bubble_surf, (bx, by))


class Calculator:
    def __init__(self):
        self.display_value = "0"
        self.previous_value = None
        self.operator = None
        self.waiting_for_operand = False
        self.just_evaluated = False
        
        # Current digit states for animation
        self.digit_states = {}  # {digit_idx: {segment: on/off}}
        self.target_digit_states = {}
        
        # Initialize digit states
        for i in range(NUM_DIGITS):
            self.digit_states[i] = {s: False for s in 'abcdefg'}
            self.target_digit_states[i] = {s: False for s in 'abcdefg'}
        
        # Sparks for segment changes
        self.sparks = []
        
        # Button press animation
        self.press_anim = {}
        
        # Last pressed indicator
        self.last_key = None
        self.indicator_timer = 0
        
        # Update display
        self.update_target_display()

    def get_display_string(self):
        """Convert display value to right-aligned string for display"""
        val = self.display_value[:NUM_DIGITS]  # Limit length
        return val.rjust(NUM_DIGITS)

    def update_target_display(self):
        """Update target segment states based on display value"""
        display_str = self.get_display_string()
        for i, char in enumerate(display_str):
            pattern = SEGMENT_PATTERNS.get(char, SEGMENT_PATTERNS[' '])
            segments = 'abcdefg'
            for j, seg in enumerate(segments):
                self.target_digit_states[i][seg] = bool(pattern[j])

    def get_segment_changes(self):
        """Get list of segments that need to change"""
        changes = []
        for i in range(NUM_DIGITS):
            for seg in 'abcdefg':
                current = self.digit_states[i][seg]
                target = self.target_digit_states[i][seg]
                if current != target:
                    changes.append((i, seg, target))
        return changes

    def apply_segment_change(self, digit_idx, segment, turn_on):
        """Apply a segment change and create sparks"""
        self.digit_states[digit_idx][segment] = turn_on
        
        # Create sparks at segment position
        dx = DIGITS_START_X + digit_idx * DIGIT_SPACING
        dy = DIGITS_START_Y
        positions = get_segment_positions(dx, dy)
        if segment in positions:
            sx, sy, is_horiz = positions[segment]
            if is_horiz:
                cx = sx + SEGMENT_LENGTH // 2
                cy = sy
            else:
                cx = sx
                cy = sy + SEGMENT_LENGTH // 2
            for _ in range(8):
                self.sparks.append(Spark(cx, cy))

    def press(self, key):
        """Handle key press"""
        self.press_anim[key] = 15
        self.last_key = key
        self.indicator_timer = 60
        
        if key in '0123456789':
            if self.waiting_for_operand or self.just_evaluated:
                self.display_value = key
                self.waiting_for_operand = False
                self.just_evaluated = False
            elif self.display_value == '0':
                self.display_value = key
            elif len(self.display_value) < NUM_DIGITS:
                self.display_value += key
                
        elif key == '.':
            if self.waiting_for_operand:
                self.display_value = '0.'
                self.waiting_for_operand = False
            elif '.' not in self.display_value:
                self.display_value += '.'
                
        elif key in '+-×÷':
            if self.operator and not self.waiting_for_operand:
                self.evaluate()
            self.previous_value = float(self.display_value)
            self.operator = key
            self.waiting_for_operand = True
            self.just_evaluated = False
            
        elif key == '=':
            self.evaluate()
            self.just_evaluated = True
            
        elif key == 'C':
            self.display_value = '0'
            self.previous_value = None
            self.operator = None
            self.waiting_for_operand = False
            self.just_evaluated = False
            
        elif key == '±':
            if self.display_value != '0':
                if self.display_value.startswith('-'):
                    self.display_value = self.display_value[1:]
                else:
                    self.display_value = '-' + self.display_value
                    
        elif key == '%':
            try:
                value = float(self.display_value)
                self.display_value = self.format_number(value / 100)
            except:
                pass
        
        self.update_target_display()

    def evaluate(self):
        """Evaluate the current operation"""
        if self.operator and self.previous_value is not None:
            try:
                current = float(self.display_value)
                if self.operator == '+':
                    result = self.previous_value + current
                elif self.operator == '-':
                    result = self.previous_value - current
                elif self.operator == '×':
                    result = self.previous_value * current
                elif self.operator == '÷':
                    if current == 0:
                        self.display_value = "Error"
                        self.operator = None
                        self.previous_value = None
                        return
                    result = self.previous_value / current
                else:
                    return
                
                self.display_value = self.format_number(result)
                self.operator = None
                self.previous_value = None
            except:
                self.display_value = "Error"

    def format_number(self, num):
        """Format number for display"""
        if num == int(num):
            formatted = str(int(num))
        else:
            formatted = f"{num:.6f}".rstrip('0').rstrip('.')
        
        if len(formatted) > NUM_DIGITS:
            if '.' in formatted:
                int_part = formatted.split('.')[0]
                if len(int_part) > NUM_DIGITS:
                    return "Error"
                decimal_places = NUM_DIGITS - len(int_part) - 1
                if decimal_places > 0:
                    formatted = f"{num:.{decimal_places}f}"
                else:
                    formatted = str(int(round(num)))
            else:
                return "Error"
        
        return formatted[:NUM_DIGITS]

    def update(self):
        # Update button animations
        for key in list(self.press_anim.keys()):
            self.press_anim[key] -= 1
            if self.press_anim[key] <= 0:
                del self.press_anim[key]
        
        # Update sparks
        for spark in self.sparks[:]:
            spark.update()
            if spark.life <= 0:
                self.sparks.remove(spark)
        
        if self.indicator_timer > 0:
            self.indicator_timer -= 1

    def draw_segment(self, surface, x, y, segment, on):
        """Draw a single seven-segment segment"""
        sw = SEGMENT_WIDTH
        sl = SEGMENT_LENGTH
        color = SEGMENT_ON if on else SEGMENT_OFF
        
        positions = get_segment_positions(x, y)
        if segment not in positions:
            return
            
        sx, sy, is_horiz = positions[segment]
        
        if is_horiz:
            # Horizontal segment
            points = [
                (sx, sy),
                (sx + sw//2, sy - sw//2),
                (sx + sl - sw//2, sy - sw//2),
                (sx + sl, sy),
                (sx + sl - sw//2, sy + sw//2),
                (sx + sw//2, sy + sw//2),
            ]
        else:
            # Vertical segment
            points = [
                (sx, sy),
                (sx - sw//2, sy + sw//2),
                (sx - sw//2, sy + sl - sw//2),
                (sx, sy + sl),
                (sx + sw//2, sy + sl - sw//2),
                (sx + sw//2, sy + sw//2),
            ]
        
        # Draw glow if on
        if on:
            glow_surf = pygame.Surface((sl + 20, sl + 20), pygame.SRCALPHA)
            glow_points = [(p[0] - sx + sl//2 + 10, p[1] - sy + sl//2 + 10) for p in points]
            pygame.draw.polygon(glow_surf, (0, 255, 80, 50), glow_points)
            surface.blit(glow_surf, (sx - sl//2 - 10, sy - sl//2 - 10))
        
        pygame.draw.polygon(surface, color, points)
        
        # Slight border
        border_color = (0, 180, 50) if on else (15, 35, 15)
        pygame.draw.polygon(surface, border_color, points, 1)

    def draw(self, surface):
        # Calculator body
        body_rect = pygame.Rect(CALC_X, CALC_Y, CALC_W, CALC_H)
        pygame.draw.rect(surface, CALC_BG, body_rect, border_radius=20)
        pygame.draw.rect(surface, CALC_BORDER, body_rect, 4, border_radius=20)
        
        # Brand strip
        strip = pygame.Rect(CALC_X + 3, CALC_Y + 3, CALC_W - 6, 25)
        pygame.draw.rect(surface, (50, 50, 80), strip, border_radius=17)
        brand = font_small.render("STICK-CALC PRO 5000", True, (150, 150, 200))
        surface.blit(brand, (CALC_X + CALC_W//2 - brand.get_width()//2, CALC_Y + 7))

        # Display frame
        frame_rect = pygame.Rect(DISPLAY_X - 5, DISPLAY_Y - 5, DISPLAY_W + 10, DISPLAY_H + 10)
        pygame.draw.rect(surface, (30, 50, 30), frame_rect, border_radius=12)
        pygame.draw.rect(surface, (60, 100, 60), frame_rect, 2, border_radius=12)
        
        # Display background
        display_rect = pygame.Rect(DISPLAY_X, DISPLAY_Y, DISPLAY_W, DISPLAY_H)
        pygame.draw.rect(surface, DISPLAY_BG, display_rect, border_radius=8)
        
        # Scanlines
        for sy in range(DISPLAY_Y + 2, DISPLAY_Y + DISPLAY_H - 2, 3):
            pygame.draw.line(surface, (10, 25, 10), 
                           (DISPLAY_X + 2, sy), (DISPLAY_X + DISPLAY_W - 2, sy), 1)

        # Draw seven-segment digits
        for i in range(NUM_DIGITS):
            dx = DIGITS_START_X + i * DIGIT_SPACING
            dy = DIGITS_START_Y
            for seg in 'abcdefg':
                on = self.digit_states[i][seg]
                self.draw_segment(surface, dx, dy, seg, on)

        # Draw operation indicator
        if self.operator:
            op_text = font_medium.render(self.operator, True, SEGMENT_ON)
            surface.blit(op_text, (DISPLAY_X + DISPLAY_W - 30, DISPLAY_Y + 10))

        # Draw sparks
        for spark in self.sparks:
            spark.draw(surface)

        # Label
        label = font_tiny.render("LCD DISPLAY - MANUAL OPERATION", True, (0, 100, 0))
        surface.blit(label, (DISPLAY_X + 5, DISPLAY_Y + DISPLAY_H - 18))

        # Current key indicator
        if self.indicator_timer > 0 and self.last_key:
            ind_text = font_tiny.render(f"INPUT: {self.last_key}", True, (0, 150, 0))
            alpha = min(255, self.indicator_timer * 8)
            ind_surf = pygame.Surface(ind_text.get_size(), pygame.SRCALPHA)
            ind_surf.fill((0, 0, 0, 0))
            ind_text.set_alpha(alpha)
            surface.blit(ind_text, (DISPLAY_X + DISPLAY_W - 70, DISPLAY_Y + 5))

        # Draw buttons
        self.draw_buttons(surface)

    def draw_buttons(self, surface):
        for label, rect in button_rects.items():
            is_pressed = label in self.press_anim
            timer = self.press_anim.get(label, 0)
            
            # Button colors based on type
            if label == 'C':
                btn_color = BUTTON_CLEAR
            elif label == '=':
                btn_color = BUTTON_EQUALS
            elif label in '+-×÷%±':
                btn_color = BUTTON_OP
            else:
                btn_color = BUTTON_COLOR
            
            if is_pressed:
                offset = min(4, int(4 * (timer / 15)))
                btn_rect = pygame.Rect(rect.x, rect.y + offset, rect.w, rect.h - offset)
                btn_color = BUTTON_PRESSED
            else:
                btn_rect = rect
            
            # Shadow
            shadow_rect = pygame.Rect(rect.x + 3, rect.y + 4, rect.w, rect.h)
            pygame.draw.rect(surface, (25, 25, 45), shadow_rect, border_radius=10)
            
            # Button
            pygame.draw.rect(surface, btn_color, btn_rect, border_radius=10)
            
            # Highlight
            if not is_pressed:
                highlight = pygame.Rect(btn_rect.x + 3, btn_rect.y + 3, btn_rect.w - 6, 12)
                h_color = tuple(min(255, c + 40) for c in btn_color)
                pygame.draw.rect(surface, h_color, highlight, border_radius=6)
            
            # Border
            pygame.draw.rect(surface, (100, 100, 150), btn_rect, 2, border_radius=10)
            
            # Text
            text_color = BLACK if is_pressed else WHITE
            text = font_medium.render(label, True, text_color)
            tx = btn_rect.x + btn_rect.w // 2 - text.get_width() // 2
            ty = btn_rect.y + btn_rect.h // 2 - text.get_height() // 2
            surface.blit(text, (tx, ty))


# Sayings for different actions
SAYINGS = {
    'digit': ["Got it!", "On it!", "Easy!", "Working!", "Fixing!", "Adjusting!"],
    'operator': ["Math time!", "Calculating...", "Let me think...", "Operator set!"],
    'equals': ["And the answer is...", "Ta-da!", "Done!", "Result ready!"],
    'clear': ["All clean!", "Fresh start!", "Cleared!", "Reset!"],
    'error': ["Oops!", "Can't do that!", "Error!"],
}


def main():
    calc = Calculator()
    stick = DisplayStickFigure()
    particles = []
    
    # Input queue
    key_queue = []
    
    # Instructions
    instructions = [
        "Press 0-9 for digits, +−×÷ for operations",
        "Press = to calculate, C to clear",
        "Watch the stick figure manually change the display!"
    ]

    running = True
    while running:
        clock.tick(FPS)

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

                # Check key mapping
                if event.key in KEY_MAP:
                    key = KEY_MAP[event.key]
                    key_queue.append(key)
                # Handle shift+= for +
                elif event.key == pygame.K_EQUALS and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    key_queue.append('+')
                # Handle shift+8 for ×
                elif event.key == pygame.K_8 and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    key_queue.append('×')

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Check button clicks
                    for label, rect in button_rects.items():
                        if rect.collidepoint(event.pos):
                            key_queue.append(label)
                            break

        # Process key queue when stick figure is free
        if key_queue and not stick.task_queue and not stick.moving and not stick.working:
            key = key_queue.pop(0)
            
            # Press the button visually
            calc.press(key)
            
            # Get segment changes needed
            changes = calc.get_segment_changes()
            
            if changes:
                # Add tasks for stick figure
                for digit_idx, segment, turn_on in changes:
                    stick.add_task(digit_idx, segment, turn_on)
                
                # Say something
                if key in '0123456789':
                    stick.say(random.choice(SAYINGS['digit']))
                elif key in '+-×÷':
                    stick.say(random.choice(SAYINGS['operator']))
                elif key == '=':
                    stick.say(random.choice(SAYINGS['equals']))
                elif key == 'C':
                    stick.say(random.choice(SAYINGS['clear']))
            else:
                # No changes needed
                if key == 'C':
                    stick.say("Already clear!")

        # Update
        calc.update()
        segment_change = stick.update(calc.get_display_string(), calc.digit_states)
        
        # Apply segment change from stick figure
        if segment_change:
            digit_idx, segment, turn_on = segment_change
            calc.apply_segment_change(digit_idx, segment, turn_on)
            # Particles
            pos = stick.get_segment_world_pos(digit_idx, segment)
            for _ in range(5):
                particles.append(Particle(pos[0], pos[1], SEGMENT_ON))

        # Update particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # Draw
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill((15, 15, 25))

        # Background pattern
        for i in range(0, WIDTH, 20):
            for j in range(0, HEIGHT, 20):
                if (i + j) % 40 == 0:
                    pygame.draw.circle(surface, (20, 20, 35), (i, j), 1)

        # Draw calculator (includes display and buttons)
        calc.draw(surface)

        # Draw stick figure (inside display area)
        stick.draw(surface)

        # Draw particles
        for p in particles:
            p.draw(surface)

        # Instructions
        inst_y = CALC_Y + CALC_H - 85
        for i, line in enumerate(instructions):
            inst_surf = font_tiny.render(line, True, (120, 120, 160))
            surface.blit(inst_surf, (CALC_X + 20, inst_y + i * 16))

        # Help text
        help_text = font_tiny.render("Click buttons or use keyboard | ESC to quit", True, (80, 80, 120))
        surface.blit(help_text, (WIDTH//2 - help_text.get_width()//2, HEIGHT - 20))

        screen.blit(surface, (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()