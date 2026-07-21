import pygame
from ntpath import join
import os
import random
from random import randint, uniform
         

def load_high_score():
    if not os.path.exists(file_name):
        return 0
    try:
        with open(file_name, "r") as file:
            return int(file.read().strip())
    except (ValueError, FileNotFoundError):
        return 0
    
def save_high_score(new_high_score):
    with open(file_name, "w") as file:
        file.write(str(new_high_score))
        
# ===========================
#      GENERAL SETUP
# ===========================
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
running = True
file_name = "highscore.txt"
clock = pygame.time.Clock()

score = 0
high_score = load_high_score()
game_state = "title_menu"

start_button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 60, 300, 80)
quit_button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 + 50, 300, 80)

resume_button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 60, 300, 80)
menu_button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 + 50, 300, 80)

countdown_value = 3
countdown_timer = 0

# difficulty scale
base_enemy_speed = 200       # start speed of mines
current_enemy_speed = base_enemy_speed

base_spawn_time = 1000     # starting spawn delay in milliseconds
min_spawn_time = 95       # max speed can spawn = lower number is more spawn
current_spawn_time = base_spawn_time

last_difficulty_update = 0

# events
mine_spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(mine_spawn_event, current_spawn_time)

difficulty_event = pygame.USEREVENT + 2
pygame.time.set_timer(difficulty_event, 8000) # how often difficulty updates (miliseconds)


# ===========================
#      IMPORTS
# ===========================
mine_surf = pygame.image.load(join('images', 'mine.png')).convert_alpha()
mine_surf = pygame.transform.scale(mine_surf, (70,70))

laser_surf = pygame.image.load(join('images', 'plasma.png')).convert_alpha()
laser_surf = pygame.transform.scale(laser_surf, (10,40))

star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
star_surf = pygame.transform.scale(star_surf, (30,30))

background_surf = pygame.image.load(join('images', 'background.png')).convert_alpha()
background_surf = pygame.transform.scale(background_surf, (WINDOW_WIDTH, WINDOW_HEIGHT))

# audio
laser_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
laser_sound.set_volume(0.25) # vol from 0 - 1

explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
explosion_sound.set_volume(0.70)

damage_sound = pygame.mixer.Sound(join('audio', 'damage.wav'))
damage_sound.set_volume(0.70)

game_music = pygame.mixer.Sound(join('audio', 'theme.wav'))
game_music.set_volume(0.4)

#  font import / redundancy
try:
    title_font_1 = pygame.font.Font(join('fonts', 'PositiveSystem.otf'), 60)  # score, hiscore txt (ingame)
    title_font_2 = pygame.font.Font(join('fonts', 'PositiveSystem.otf'), 100) # you suck txt
    title_font_3 = pygame.font.Font(join('fonts', 'PositiveSystem.otf'), 150) # title
    sub_font_1 = pygame.font.Font(join('fonts', 'Gameplay.ttf'), 35) # score results (game over)
    sub_font_2 = pygame.font.Font(join('fonts', 'Gameplay.ttf'), 20) # restart, exit
    sub_font_3 = pygame.font.Font(join('fonts', 'Gameplay.ttf'), 36) # start menu buttons
    font = pygame.font.Font(join('fonts', 'Gameplay.ttf'), 45) # score, hiscore val (ingame)
    print("Font loaded successfuly!")

except FileNotFoundError:
    font = pygame.font.SysFont('Arial', 45, bold=True)
    title_font_1 = pygame.font.SysFont('Arial', 45, bold=True)
    title_font_2 = pygame.font.SysFont('Arial', 45, bold=True)
    title_font_3 = pygame.font.SysFont('Arial', 45, bold=True)
    sub_font_1 = pygame.font.SysFont('Arial', 45, bold=True)
    sub_font_2 = pygame.font.SysFont('Arial', 45, bold=True)
    print("Warning: Custom font not found. Falling back to Arial.")
    
# explosion anim
explosion_frames = []
for i in range(1, 12):
    filename = f'explosion_1_{i:02d}.png'
    frame = pygame.image.load(join('images', filename)).convert_alpha()
    frame = pygame.transform.scale(frame, (120,120))
    explosion_frames.append(frame)   
    
player_explosion = []
for i in range(1, 10):
    filename = f'explosion_3_{i:02d}.png'
    frame = pygame.image.load(join('images', filename)).convert_alpha()
    frame = pygame.transform.scale(frame, (100, 100))
    player_explosion.append(frame) 


# ===========================
#      SPRITE CLASSES
# ===========================
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.idle_image = pygame.image.load(join('images', 'player.png'))
        self.image = self.idle_image
        self.rect = self.image.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))

       
        # animation setup
        self.frames_left = []
        self.frames_right = []
        for i in range(1,3):
            img_left = pygame.image.load(join('images', f'player_L_{i}.png')).convert_alpha()
            img_right = pygame.image.load(join('images', f'player_R_{i}.png')).convert_alpha()
            self.frames_left.append(img_left)
            self.frames_right.append(img_right)
            
        self.frame_index = 0
        self.animation_speed = 10 # fps
        self.state = 'idle'
        
        self.direction = pygame.Vector2()
        self.speed = 500
        
        # laser cooldown
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400  # fire rate timer milliseconds
        
        # health setup
        self.max_health = 100
        self.current_health = 100
        self.health_bar_length = 200 # size of health bar
        
        
    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True
    
    def animate(self,dt):
        if self.direction.x < 0:
            self.state = 'left'
        elif self.direction.x > 0:
            self.state = 'right'
        else:
            self.state = 'idle'
        
        if self.state == 'left':
            self.frame_index += self.animation_speed * dt
            if self.frame_index >= len(self.frames_left):
                self.frame_index = 0
            self.image = self.frames_left[int(self.frame_index)]
        
        elif self.state == 'right':
            self.frame_index += self.animation_speed * dt
            if self.frame_index >= len(self.frames_right):
                self.frame_index = 0
            self.image = self.frames_right[int(self.frame_index)]
            
        else:
            self.image = self.idle_image
            self.frame_index = 0
            
    def update(self, dt):
        if not game_state == "playing":
            self.direction = pygame.Vector2(0,0)
            self.animate(dt)
            return
        
        # keyboard controls    
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.center += self.direction * self.speed * dt
        
        # block from going off screen
        self.rect.centerx = max(self.rect.width / 2, min(self.rect.centerx, WINDOW_WIDTH - self.rect.width / 2))
        self.rect.centery = max(self.rect.height / 2, min(self.rect.centery, WINDOW_HEIGHT - self.rect.height / 2))
        
        # mouse controls
        mouse_click = pygame.mouse.get_just_pressed()
        if mouse_click[0] and self.can_shoot:
           Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
           self.laser_shoot_time = pygame.time.get_ticks()
           laser_sound.play()
        
        self.laser_timer()
        self.animate(dt)
          
class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        x =random.randint(0, WINDOW_WIDTH - self.image.get_width())
        y = random.randint(0, WINDOW_HEIGHT - self.image.get_height())
        self.rect = self.image.get_frect(topleft=(x, y))
        self.alpha = randint(30, 255)
        self.speed = random.choice([-1, -2, 1, 2])
        self.base_image = surf
        
    def update(self, dt):
        # update transparency
        self.alpha += self.speed * dt * 50
        
        # fancy star flashing
        if self.alpha <= 20:
            self.alpha = 20
            self.speed *= -1 
        elif self.alpha >= 255:
            self.alpha = 255
            self.speed *= -1 

        # transparency of star
        self.image = self.image.copy()
        self.image.set_alpha(self.alpha)

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom = pos)
    
    def update(self, dt):
        self.rect.centery -= 750 * dt  # laser speed milliseconds
        if self.rect.bottom < 0:
            self.kill()

class Mine(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups, speed):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 4600
        self.direction = pygame.Vector2(uniform(-0.5, 0.5),1)
        self.speed = speed
        
    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt 
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()
        if self.rect.right < -100 or self.rect.left > WINDOW_WIDTH + 100:
            self.kill()
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center = pos)
        self.animation_speed = 15 # fps
    def update(self, dt):
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]

class PlayerExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center = pos)
        self.animation_speed = 15 # fps
    def update(self, dt):
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]

# ===========================
#      LOAD SPRITES
# ===========================
all_sprites = pygame.sprite.Group()
mine_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
star_sprites = pygame.sprite.Group()

for _ in range(30):
    Star((all_sprites, star_sprites), star_surf)
player = Player(all_sprites)

# mine event
pygame.time.set_timer(mine_spawn_event, base_spawn_time)

# ====================================
#    GAME STATE / LOGIC / MECHANICS
# ====================================

def reset_game():
    global score, game_state, current_enemy_speed, current_spawn_time
    score = 0
    game_state = "playing"
    
    # reset stats
    player.current_health = player.max_health
    player.rect.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
    player.direction = pygame.Vector2()
    player.can_shoot = True
    
    # reset difficulty
    current_enemy_speed = base_enemy_speed
    current_spawn_time = base_spawn_time
    pygame.time.set_timer(mine_spawn_event, current_spawn_time)
    
    # clear sprites - not stars
    mine_sprites.empty()
    laser_sprites.empty()
    for sprite in all_sprites:
        if sprite != player and not isinstance(sprite, Star):
            sprite.kill()
            
    clock.tick()
    
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
                     
def collisions():
    
    global score, game_state, high_score, player
    
    # player collision
    collision_sprites = pygame.sprite.spritecollide(player, mine_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        player.current_health -= len(collision_sprites) * 20
        PlayerExplosion(player_explosion, player.rect.center, all_sprites)
        
        for mine in collision_sprites:
            Explosion(explosion_frames, mine.rect.center, all_sprites)
            damage_sound.play()

        if player.current_health <= 0:
            player.current_health = 0
            game_state = "game_over"
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        
        if score > high_score:
            high_score = score
            save_high_score(high_score)
            
            
    # laser collision    
    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, mine_sprites, True, pygame.sprite.collide_mask)
        if collided_sprites:
            score += len(collided_sprites) * 10
            for mine in collided_sprites:
                Explosion(explosion_frames, mine.rect.center, all_sprites)
            laser.kill()
            explosion_sound.play()

def display_score():
    
    # current score
    score_label = title_font_1.render('SCORE ', True, 'cadetblue')
    display_surface.blit(score_label, (40, 80))
    score_val_surf = font.render(str(score), True, 'darkslategray2')
    display_surface.blit(score_val_surf, (50 + score_label.get_width(), 80))
    
    # high score
    hs_label = title_font_1.render('BEST  ', True, 'darkslategray2')
    hs_surf = font.render(str(high_score), True, 'goldenrod3')
    hs_x = WINDOW_WIDTH - hs_label.get_width() - hs_surf.get_width() - 40
    display_surface.blit(hs_label, (hs_x, 40))
    display_surface.blit(hs_surf, (hs_x + hs_label.get_width(), 40))
    
def draw_health_bar():
    # bar location
    bar_x = 40
    bar_y = 40
    bar_height = 25
    
    health_ratio = player.current_health / player.max_health
    dynamic_width = int(player.health_bar_length * health_ratio)
    
    # draw container
    background_rect = pygame.FRect(bar_x, bar_y, player.health_bar_length, bar_height)
    pygame.draw.rect(display_surface, 'indianred4', background_rect)
    # health
    health_rect = pygame.FRect(bar_x, bar_y, dynamic_width, bar_height)
    pygame.draw.rect(display_surface, 'seagreen4', health_rect)
    
    pygame.draw.rect(display_surface, 'grey14', background_rect, 3)

def display_game_over():
    
    global high_score
    
    # blur screen
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    display_surface.blit(overlay, (0, 0))
    
    title_surf = title_font_2.render("Wow, you suck!", True, 'darkslategray1')
    title_rect = title_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 100))
    display_surface.blit(title_surf, title_rect)
    
    results_text = f"Final Score: {score}  |  Best: {high_score}"
    results_surf = sub_font_1.render(results_text, True, 'goldenrod3' if score >= high_score else 'darkslategray3')
    results_rect = results_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 5))
    display_surface.blit(results_surf, results_rect)
    
    restart_surf = sub_font_2.render("Press 'r' to try again", True, 'cadetblue')
    restart_rect = restart_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50))
    display_surface.blit(restart_surf, restart_rect)
    
    exit_surf = sub_font_2.render("Press 'ESC' to exit", True, 'cadetblue')
    exit_rect = exit_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 80))
    display_surface.blit(exit_surf, exit_rect)

def display_start_menu():
    # background
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    display_surface.blit(overlay, (0, 0))
    
    # title text
    title_surf = title_font_3.render("Viatorem", True, 'darkslategray1')
    title_rect = title_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 150))
    display_surface.blit(title_surf, title_rect)
    
    # buttons rects
    pygame.draw.rect(display_surface, 'cadetblue4', start_button_rect, border_radius=18)
    pygame.draw.rect(display_surface, 'cadetblue4', quit_button_rect, border_radius=18)
    
    # button text
    start_text = sub_font_3.render("START GAME", False, 'paleturquoise')
    quit_text = sub_font_3.render("QUIT", False, 'darkslategray')
    
    display_surface.blit(start_text, start_text.get_frect(center=start_button_rect.center))
    display_surface.blit(quit_text, quit_text.get_frect(center=quit_button_rect.center))    
    
    panel_width, panel_height = 325, 160
    panel_x = WINDOW_WIDTH // 2 - panel_width // 2
    panel_y = WINDOW_HEIGHT - panel_height - 40 # from bottom edge
    
    # background
    control_panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    control_panel.fill((20, 30, 40, 160))
    display_surface.blit(control_panel, (panel_x, panel_y))
    
    # cntrl panel outline
    pygame.draw.rect(display_surface, 'cadetblue4', (panel_x, panel_y, panel_width, panel_height), width=2, border_radius=8)
    
    # cntrl txt
    header_surf = sub_font_2.render("-- CONTROLS --", False, 'goldenrod2')
    move_surf   = sub_font_2.render("MOVE:   W   A   S   D", False, 'paleturquoise')
    shoot_surf  = sub_font_2.render("SHOOT:  LEFT CLICK ", False, 'paleturquoise')
    pause_surf  = sub_font_2.render("PAUSE:  ESC  ", False, 'paleturquoise')
    
    # show txt
    display_surface.blit(header_surf, header_surf.get_frect(center=(WINDOW_WIDTH // 2, panel_y + 25)))
    display_surface.blit(move_surf,   move_surf.get_frect(center=(WINDOW_WIDTH // 2, panel_y + 65)))
    display_surface.blit(shoot_surf,  shoot_surf.get_frect(center=(WINDOW_WIDTH // 2, panel_y + 100)))
    display_surface.blit(pause_surf,  pause_surf.get_frect(center=(WINDOW_WIDTH // 2, panel_y + 135)))
    
def display_pause_menu():
    # background
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) # 150 opacity makes it darker than the start menu
    display_surface.blit(overlay, (0, 0))
    
    # pause title
    pause_surf = title_font_2.render("GAME PAUSED", True, 'darkslategray1')
    pause_rect = pause_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 150))
    display_surface.blit(pause_surf, pause_rect)
    
    # buttons
    pygame.draw.rect(display_surface, 'cadetblue4', resume_button_rect, border_radius=18)
    pygame.draw.rect(display_surface, 'cadetblue4', menu_button_rect, border_radius=18)
    
    # buttons text
    resume_text = sub_font_3.render("RESUME", True, 'paleturquoise')
    menu_text = sub_font_3.render("MAIN MENU", True, 'paleturquoise')
    
    display_surface.blit(resume_text, resume_text.get_frect(center=resume_button_rect.center))
    display_surface.blit(menu_text, menu_text.get_frect(center=menu_button_rect.center))    
    
game_music.play(-1)
    
# ===========================
#      EVENT LOOP
# ===========================   
while running:
    dt = clock.tick() / 1000
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # START MENU
        if game_state == "title_menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button_rect.collidepoint(event.pos):
                    reset_game() 
                elif quit_button_rect.collidepoint(event.pos):
                    running = False
                    
        # PLAYING
        elif game_state == "playing":
    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "paused"
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
    
            if event.type == mine_spawn_event:
                x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
                Mine(mine_surf, (x, y), (all_sprites, mine_sprites), current_enemy_speed)
        
        # difficulty loop
            if event.type == difficulty_event:
                current_enemy_speed += 25  # bigger number = faster moving mines
                current_spawn_time = max(min_spawn_time, current_spawn_time - 50)  # bigger number = more spawn
                pygame.time.set_timer(mine_spawn_event, current_spawn_time)
        
        # PAUSED
        elif game_state == "paused":
            # press ESC to resume
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "countdown"
                    countdown_timer = pygame.time.get_ticks()
                    countdown_value = 3
                    
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
            
            # click ability while paused
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if resume_button_rect.collidepoint(event.pos):
                    game_state = "countdown"
                    
                    countdown_timer = pygame.time.get_ticks()
                    countdown_value = 3
                    
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                
                elif menu_button_rect.collidepoint(event.pos):
                    game_state = "title_menu"

           
        # GAME OVER
        elif game_state == "game_over":   
           
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
 
    # updates based on state
    if game_state == "playing":
        game_music.set_volume(0.4)
        all_sprites.update(dt)
        collisions()
    
    elif game_state == "countdown":
        game_music.set_volume(0.3)
        current_time = pygame.time.get_ticks()
        time_elapsed = current_time - countdown_timer
        
        if time_elapsed < 1000:
            countdown_value = 3
        elif time_elapsed < 2000:
            countdown_value = 2
        elif time_elapsed < 3000:
            countdown_value = 1
        else:
            game_state = "playing"
            clock.tick()
    
    elif game_state == "title_menu":
        game_music.set_volume(0.2)
        star_sprites.update(dt) 
    
    elif game_state == "paused":
        game_music.set_volume(0.1)
    
    elif game_state == "game_over":
        game_music.set_volume(0.2)
        star_sprites.update(dt)
         
    # render game
    pygame.display.set_caption('Viatorem')
    display_surface.fill('darkgray')
    display_surface.blit(background_surf, (0,0))
    
    all_sprites.draw(display_surface)
    
    if game_state == "playing":
        display_score()
        draw_health_bar()
    
    elif game_state == "countdown":
        display_score()
        draw_health_bar()
        
        # draw countdown timer
        countdown_surf = title_font_3.render(str(countdown_value), True, 'darkslategray1')
        countdown_rect = countdown_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        display_surface.blit(countdown_surf, countdown_rect)
        
        
    elif game_state == "title_menu":
        display_start_menu()
        
    elif game_state == "paused":
        display_score()
        draw_health_bar()
        display_pause_menu()
        
    elif game_state == "game_over":
        display_game_over()
    
    
    pygame.display.update()
pygame.quit()    
