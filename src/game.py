import sys
import random
import pygame
import json
import os
import math

# Space Flappy
# Drawn shapes only (no external assets). Spacebar to thrust.

BASE_W, BASE_H = 288, 512
SCALE = 2
W, H = BASE_W * SCALE, BASE_H * SCALE

FPS = 60

GRAVITY = 0.2  # Slowed down for testing (was 0.5)
JUMP_VEL = -6  # Gentler jump for testing (was -8)
PIPE_SPEED = 1.5  # Slower pipes for testing (was 2.5)
PIPE_GAP = 150  # Wider gap for testing (was 120)
PIPE_FREQ = 1500  # ms
BUILDING_SPEED = PIPE_SPEED * 0.35
# small anti-gravity factor: reduces downward acceleration slightly
ANTI_GRAVITY = 0.15
TERMINAL_VEL = 12

# lives
STARTING_LIVES = 5

# coins
COIN_FREQ = 2000  # ms between coin spawns
COIN_VALUE = 5

# animation
frame_count = 0

# leaderboard
LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'leaderboard.json')
MAX_LEADERBOARD = 5

# Globals set in main()
screen = None
clock = None
font = None


class Bird:
    def __init__(self):
        self.x = 72
        self.y = BASE_H // 2
        self.vel = 0
        self.size = 12

    def jump(self):
        self.vel = JUMP_VEL

    def update(self):
        # apply gravity; when falling reduce gravity a bit to simulate 'anti-grav'
        if self.vel > 0:
            self.vel += GRAVITY * (1.0 - ANTI_GRAVITY)
        else:
            self.vel += GRAVITY

        # cap downward speed
        if self.vel > TERMINAL_VEL:
            self.vel = TERMINAL_VEL

        self.y += self.vel

        if self.y < 0:
            self.y = 0
            self.vel = 0

    def get_rect(self):
        s = self.size
        return pygame.Rect(int(self.x - s), int(self.y - s), s * 2, s * 2)

    def draw(self, surf, invincible=False):
        global frame_count
        # draw a retro spaceship: red and blue with animated thruster
        r = self.get_rect()
        cx = r.x + r.w // 2
        cy = r.y + r.h // 2
        
        # Calculate tilt based on velocity (-15 to +15 degrees)
        tilt = max(-15, min(15, self.vel * 3))
        
        # Flash effect when invincible
        if invincible and (frame_count // 5) % 2 == 0:
            body_color = (255, 200, 200)
            cockpit_color = (200, 200, 255)
        else:
            body_color = (220, 50, 50)
            cockpit_color = (50, 100, 220)
        
        # Create a surface to draw the ship on (for rotation)
        ship_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        ship_cx, ship_cy = 20, 20
        
        # Main body (red)
        pygame.draw.rect(ship_surf, body_color, (8, 10, 20, 20))
        
        # Cockpit (blue dome)
        pygame.draw.ellipse(ship_surf, cockpit_color, (22, 12, 12, 16))
        
        # Nose cone (blue triangle pointing right)
        nose = [(38, ship_cy), (28, 8), (28, 32)]
        pygame.draw.polygon(ship_surf, cockpit_color, nose)
        
        # Wings (red triangles)
        top_wing = [(12, 10), (12, 2), (24, 10)]
        pygame.draw.polygon(ship_surf, body_color, top_wing)
        bot_wing = [(12, 30), (12, 38), (24, 30)]
        pygame.draw.polygon(ship_surf, body_color, bot_wing)
        
        # Animated thruster flame
        flame_size = 6 + (frame_count % 4) * 2  # Flickering size
        flame_colors = [(255, 100, 50), (255, 200, 50), (100, 150, 255)]
        flame_color = flame_colors[(frame_count // 3) % 3]
        flame = [(8, ship_cy - 4), (8 - flame_size, ship_cy), (8, ship_cy + 4)]
        pygame.draw.polygon(ship_surf, flame_color, flame)
        
        # Rotate the ship based on tilt
        rotated = pygame.transform.rotate(ship_surf, -tilt)
        rot_rect = rotated.get_rect(center=(cx, cy))
        surf.blit(rotated, rot_rect.topleft)


class PipePair:
    """Laser beam obstacles"""
    def __init__(self, x):
        self.x = x
        self.w = 20  # Thinner laser beams
        self.gap = PIPE_GAP
        self.top = random.randint(40, BASE_H - 40 - self.gap)
        self.pulse_offset = random.randint(0, 60)  # Random pulse phase

    def update(self):
        self.x -= PIPE_SPEED

    def offscreen(self):
        return self.x + self.w < -10

    def collides(self, r: pygame.Rect):
        top_rect = pygame.Rect(int(self.x), 0, self.w, int(self.top))
        bottom_rect = pygame.Rect(int(self.x), int(self.top + self.gap), self.w, BASE_H - int(self.top + self.gap))
        return r.colliderect(top_rect) or r.colliderect(bottom_rect)

    def draw(self, surf):
        global frame_count
        # Pulsing laser beams - red/orange glow
        pulse = abs(math.sin((frame_count + self.pulse_offset) * 0.1)) * 0.4 + 0.6
        
        x = int(self.x)
        w = int(self.w)
        
        # Core beam color (bright red/orange)
        core_r = int(255 * pulse)
        core_g = int(100 * pulse)
        core_color = (core_r, core_g, 20)
        
        # Outer glow color (darker red)
        glow_color = (int(150 * pulse), 30, 30)
        
        # Top laser beam
        top_h = int(self.top)
        # Glow (wider)
        pygame.draw.rect(surf, glow_color, (x - 4, 0, w + 8, top_h))
        # Core (narrower, brighter)
        pygame.draw.rect(surf, core_color, (x + 2, 0, w - 4, top_h))
        # Emitter at bottom of top beam
        pygame.draw.ellipse(surf, (255, 255, 200), (x - 6, top_h - 10, w + 12, 20))
        
        # Bottom laser beam
        bot_y = int(self.top + self.gap)
        bot_h = BASE_H - bot_y
        # Glow
        pygame.draw.rect(surf, glow_color, (x - 4, bot_y, w + 8, bot_h))
        # Core
        pygame.draw.rect(surf, core_color, (x + 2, bot_y, w - 4, bot_h))
        # Emitter at top of bottom beam
        pygame.draw.ellipse(surf, (255, 255, 200), (x - 6, bot_y - 10, w + 12, 20))


def draw_background(surf):
    # Deep space gradient background
    for y in range(BASE_H):
        # Gradient from dark blue at top to black at bottom
        ratio = y / BASE_H
        r = int(5 * (1 - ratio))
        g = int(10 * (1 - ratio))
        b = int(30 * (1 - ratio) + 5)
        pygame.draw.line(surf, (r, g, b), (0, y), (BASE_W, y))


def generate_stars(count, layer):
    """Generate stars for a parallax layer. Layer 0 = far (slow), 2 = near (fast)"""
    stars = []
    for _ in range(count):
        x = random.randint(0, BASE_W * 2)
        y = random.randint(0, BASE_H)
        # Size and brightness based on layer
        if layer == 0:  # Far stars - small, dim
            size = 1
            brightness = random.randint(80, 120)
        elif layer == 1:  # Mid stars
            size = random.choice([1, 2])
            brightness = random.randint(120, 180)
        else:  # Near stars - larger, brighter
            size = random.choice([2, 3])
            brightness = random.randint(180, 255)
        color = (brightness, brightness, brightness + random.randint(0, 20))
        stars.append({'x': x, 'y': y, 'size': size, 'color': color})
    return stars


def draw_stars(surf, star_layers, offsets):
    """Draw parallax star layers"""
    for layer_idx, stars in enumerate(star_layers):
        offset = offsets[layer_idx]
        total_w = BASE_W * 2
        for star in stars:
            x = (star['x'] - offset) % total_w
            if x > BASE_W:
                continue
            pygame.draw.rect(surf, star['color'], (int(x), star['y'], star['size'], star['size']))


class Coin:
    """Collectible coin that spins and gives bonus points"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 10
        self.collected = False
        self.spin_offset = random.randint(0, 60)
    
    def update(self):
        self.x -= PIPE_SPEED
    
    def offscreen(self):
        return self.x + self.size < -10
    
    def collides(self, r: pygame.Rect):
        coin_rect = pygame.Rect(int(self.x - self.size), int(self.y - self.size), 
                                self.size * 2, self.size * 2)
        return r.colliderect(coin_rect)
    
    def draw(self, surf):
        global frame_count
        if self.collected:
            return
        
        # Spinning coin effect - width varies with sin wave
        spin = abs(math.sin((frame_count + self.spin_offset) * 0.15))
        width = max(2, int(self.size * spin))
        
        # Gold color with shimmer
        shimmer = int(50 * spin)
        color = (255, 200 + shimmer, 50)
        
        # Draw ellipse (appears to spin)
        pygame.draw.ellipse(surf, color, 
                           (int(self.x - width), int(self.y - self.size), 
                            width * 2, self.size * 2))
        # Inner shine
        if spin > 0.5:
            pygame.draw.ellipse(surf, (255, 255, 200), 
                               (int(self.x - width//2), int(self.y - self.size//2), 
                                width, self.size))


def scale_surface(surf):
    return pygame.transform.scale(surf, (W, H))


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_leaderboard(board):
    try:
        os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(board, f, indent=2)
    except:
        pass  # Silently fail if can't save


def is_high_score(score, board):
    if len(board) < MAX_LEADERBOARD:
        return True
    return score > board[-1]['score']


def add_to_leaderboard(name, score, board):
    board.append({'name': name, 'score': score})
    board.sort(key=lambda x: x['score'], reverse=True)
    return board[:MAX_LEADERBOARD]


def draw_leaderboard(surf, board, highlight_score=None):
    title_font = pygame.font.SysFont('Arial', 24 * SCALE, bold=True)
    entry_font = pygame.font.SysFont('Arial', 18 * SCALE)

    title = title_font.render('LEADERBOARD', True, (255, 255, 255))
    surf.blit(title, (BASE_W // 2 - title.get_width() // 2, 80))

    y = 120
    for i, entry in enumerate(board):
        color = (255, 215, 0) if entry['score'] == highlight_score else (255, 255, 255)
        rank = f"{i+1}. {entry['name'][:10]:<10} {entry['score']:>4}"
        text = entry_font.render(rank, True, color)
        surf.blit(text, (BASE_W // 2 - text.get_width() // 2, y))
        y += 30


def main():
    global screen, clock, font, frame_count
    
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Space Flappy')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 18 * SCALE)
    
    surface = pygame.Surface((BASE_W, BASE_H))
    # pre-render static background (space gradient) to a surface
    bg = pygame.Surface((BASE_W, BASE_H))
    draw_background(bg)
    bird = Bird()
    pipes = []
    coins = []
    coin_score = 0
    score = 0
    running = True
    game_over = False
    
    # Space background - 3 parallax star layers
    star_layers = [
        generate_stars(50, 0),   # Far layer (slow)
        generate_stars(30, 1),   # Mid layer
        generate_stars(20, 2),   # Near layer (fast)
    ]
    star_speeds = [PIPE_SPEED * 0.2, PIPE_SPEED * 0.4, PIPE_SPEED * 0.7]
    star_offsets = [0.0, 0.0, 0.0]

    # leaderboard state
    leaderboard = load_leaderboard()
    entering_name = False
    player_name = ''
    name_submitted = False
    
    # lives
    lives = STARTING_LIVES
    invincible_timer = 0  # brief invincibility after losing a life

    pygame.time.set_timer(pygame.USEREVENT + 1, PIPE_FREQ)
    pygame.time.set_timer(pygame.USEREVENT + 2, COIN_FREQ)

    while running:
        frame_count += 1
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over:
                        # restart
                        bird = Bird()
                        pipes = []
                        coins = []
                        coin_score = 0
                        score = 0
                        lives = STARTING_LIVES
                        invincible_timer = 0
                        game_over = False
                        entering_name = False
                        player_name = ''
                        name_submitted = False
                        leaderboard = load_leaderboard()
                        star_offsets = [0.0, 0.0, 0.0]
                    else:
                        bird.jump()
                elif entering_name:
                    # handle name input
                    if event.key == pygame.K_RETURN:
                        if player_name.strip():
                            leaderboard = add_to_leaderboard(player_name.strip(), score + coin_score, leaderboard)
                            save_leaderboard(leaderboard)
                            entering_name = False
                            name_submitted = True
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.unicode.isprintable() and len(player_name) < 15:
                        player_name += event.unicode
            elif event.type == pygame.USEREVENT + 1 and not game_over:
                pipes.append(PipePair(BASE_W + 10))
            elif event.type == pygame.USEREVENT + 2 and not game_over:
                # Spawn coin at random height in playable area
                coin_y = random.randint(60, BASE_H - 60)
                coins.append(Coin(BASE_W + 20, coin_y))

        if not game_over:
            bird.update()
            # update pipes
            for p in pipes:
                p.update()
            
            # update coins
            for c in coins:
                c.update()

            # update parallax star layers
            for i in range(len(star_offsets)):
                star_offsets[i] = (star_offsets[i] + star_speeds[i]) % (BASE_W * 2)

            # remove offscreen pipes and coins
            pipes = [p for p in pipes if not p.offscreen()]
            coins = [c for c in coins if not c.offscreen() and not c.collected]

            # scoring: when pipe passes bird x and not counted
            for p in pipes:
                if not hasattr(p, 'passed') and p.x + p.w < bird.x:
                    p.passed = True
                    score += 1
            
            # coin collection
            r = bird.get_rect()
            for c in coins:
                if not c.collected and c.collides(r):
                    c.collected = True
                    coin_score += COIN_VALUE

            # collisions
            hit = False
            
            if invincible_timer > 0:
                invincible_timer -= 1
            else:
                if bird.y + bird.size * 2 >= BASE_H:
                    hit = True
                for p in pipes:
                    if p.collides(r):
                        hit = True
                        break
            
            if hit:
                lives -= 1
                if lives <= 0:
                    game_over = True
                    if is_high_score(score + coin_score, leaderboard) and not name_submitted:
                        entering_name = True
                else:
                    # Reset bird position, keep score and pipes
                    bird = Bird()
                    invincible_timer = 90  # 1.5 seconds of invincibility

        # draw everything on base surface (use pre-rendered background)
        surface.blit(bg, (0, 0))
        draw_stars(surface, star_layers, star_offsets)

        # draw coins
        for c in coins:
            c.draw(surface)

        # draw pipes (laser beams)
        for p in pipes:
            p.draw(surface)

        # draw spaceship
        bird.draw(surface, invincible_timer > 0)

        # HUD - space themed colors
        total_score = score + coin_score
        score_surf = font.render(f'Score: {total_score}', True, (100, 255, 255))
        surface.blit(score_surf, (BASE_W // 2 - score_surf.get_width() // 2, 8))
        
        # Lives display
        lives_text = font.render(f'Lives: {lives}', True, (255, 100, 100))
        surface.blit(lives_text, (8, 8))
        
        # Coins collected
        coin_text = font.render(f'Coins: {coin_score // COIN_VALUE}', True, (255, 215, 0))
        surface.blit(coin_text, (BASE_W - coin_text.get_width() - 8, 8))

        if game_over:
            if entering_name:
                # name entry UI
                prompt = font.render('NEW HIGH SCORE!', True, (255, 215, 0))
                surface.blit(prompt, (BASE_W // 2 - prompt.get_width() // 2, 40))

                name_prompt = font.render('Enter your name:', True, (255, 255, 255))
                surface.blit(name_prompt, (BASE_W // 2 - name_prompt.get_width() // 2, 180))

                # name input box
                name_display = player_name + '_'
                name_text = font.render(name_display, True, (255, 255, 0))
                surface.blit(name_text, (BASE_W // 2 - name_text.get_width() // 2, 220))

                hint = font.render('Press ENTER to submit', True, (180, 180, 180))
                surface.blit(hint, (BASE_W // 2 - hint.get_width() // 2, 280))
            else:
                # show leaderboard
                draw_leaderboard(surface, leaderboard, score if name_submitted else None)

                go = font.render('GAME OVER - Press SPACE to restart', True, (255, 50, 50))
                surface.blit(go, (BASE_W // 2 - go.get_width() // 2, BASE_H - 60))

        # scale and blit
        screen.blit(scale_surface(surface), (0, 0))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
