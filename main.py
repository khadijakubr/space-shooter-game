import pygame
from os.path import join
from random import randint, uniform
import asyncio

# pygame setup
pygame.init()
window_width, window_height = 1280, 720 
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Space Shooter")
running = True
game_active = True  # Flag untuk status game (aktif atau game over)
clock = pygame.time.Clock()

#Imports images
star_surf = pygame.image.load(join("Image", "star.png")).convert_alpha()
meteor_surf = pygame.image.load(join("Image", "meteor.png")).convert_alpha()
laser_surf = pygame.image.load(join("Image", "laser.png")).convert_alpha()
font = pygame.font.Font(join("font", "Oxanium-Bold.ttf"), 30)
explosion_frames = [pygame.image.load(join("Image", "explosion", f'{i}.png')).convert_alpha() for i in range(21)]

#Imports sounds
laser_sound = pygame.mixer.Sound(join("audio", "laser.wav"))
laser_sound.set_volume(0.3)

explosion_sound = pygame.mixer.Sound(join("audio", "explosion.wav"))
explosion_sound.set_volume(0.3)

game_music = pygame.mixer.Sound(join("audio", "game_music.wav"))
game_music.set_volume(0.2)
game_music.play(loops = -1)

#Class list
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join("Image", "player.png")).convert_alpha()
        self.rect = self.image.get_frect(center=(window_width / 2, window_height / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 300

        #cooldown for laser
        self.can_shoot = True
        self.laser_shoot_time = 0  # Perbaikan: nama variabel yang benar
        self.laser_cooldown = 500

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.laser_cooldown:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction.magnitude() != 0 else self.direction
        self.rect.center += self.direction * self.speed * dt

        # Keep the player within the screen bounds
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > window_width:
            self.rect.right = window_width
        elif self.rect.top < 0:
            self.rect.top = 0
        elif self.rect.bottom > window_height:
            self.rect.bottom = window_height
    
        # Perbaikan: Gunakan pengecekan penekanan Space yang lebih standard
        if keys[pygame.K_SPACE] and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            laser_sound.play()
            
        # Panggil timer laser untuk mengelola cooldown
        self.laser_timer()

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center=(randint(0, window_width), randint(0, window_height)))

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom = pos)
    
    def update(self, dt):
        self.rect.centery -= 600 * dt
        if self.rect.bottom < 0:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 2500
        self.direction = pygame.math.Vector2(uniform(-1, 1), 1)
        self.speed = randint(400, 500)
        self.rotation_speed = randint(50, 60)
        self.rotation = 0

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_frect(center = self.rect.center)
        
class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_frect(center = pos)
    
    def update(self, dt):
        self.index += 20 * dt 
        if self.index < len(self.frames):  # Perbaikan: gunakan < bukan <=
            self.image = self.frames[int(self.index)]
        else:
            self.kill()
        
#Function List
def collision_handler():
    global game_active, final_score, start_time

    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, False, pygame.sprite.collide_mask)
    if collision_sprites and game_active:
        # Buat efek ledakan saat player dihantam meteor
        AnimatedExplosion(explosion_frames, player.rect.center, all_sprites)
        explosion_sound.play()
        game_active = False
        final_score = (pygame.time.get_ticks() - start_time) // 100
        game_music.stop()  # Hentikan musik saat game over

    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collided_sprites:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            explosion_sound.play()

def display_score():
    global score, start_time
    score = (pygame.time.get_ticks() - start_time) // 100
    text_surf = font.render(f"Score: {score}", True, (255, 255, 255))
    text_rect = text_surf.get_frect(midbottom = (window_width / 2, window_height - 50))
    screen.blit(text_surf, text_rect)
    pygame.draw.rect(screen, (240, 240, 240), text_rect.inflate(30, 30).move(0, -5), 5, 10)

def display_game_over_screen():
    text_surf = font.render(f"GAME OVER", True, (255, 255, 255))
    text_rect = text_surf.get_frect(center = (window_width / 2, window_height / 2 - 50))
    screen.blit(text_surf, text_rect)
    
    score_surf = font.render(f"Final Score: {final_score}", True, (255, 255, 255))
    score_rect = score_surf.get_frect(center = (window_width / 2, window_height / 2))
    screen.blit(score_surf, score_rect)
    
    retry_surf = font.render("Press R to Restart", True, (255, 255, 255))
    retry_rect = retry_surf.get_frect(center = (window_width / 2, window_height / 2 + 50))
    screen.blit(retry_surf, retry_rect)
    
    exit_surf = font.render("Press ESC to Exit", True, (255, 255, 255))
    exit_rect = exit_surf.get_frect(center = (window_width / 2, window_height / 2 + 100))
    screen.blit(exit_surf, exit_rect)

def reset_game():
    global game_active, final_score, score, start_time
    
    # Reset all sprites
    all_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    
    # Regenerate player and stars
    global stars, player
    stars = [Star(all_sprites, star_surf) for _ in range(20)]
    player = Player(all_sprites)
    
    # Reset game variables
    game_active = True
    score = 0
    final_score = 0
    start_time = pygame.time.get_ticks()
    
    # Restart music
    game_music.play(loops = -1)

#Initialize sprites
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
stars = [Star(all_sprites, star_surf) for _ in range(20)]
player = Player(all_sprites)

#Customs events
meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, 500)

# Variabel for game over
score = 0
final_score = 0
start_time = pygame.time.get_ticks()  

# This is the main loop of the game
async def main():
    while running:
        dt = clock.tick(60) / 1000  #Delta time
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == meteor_event and game_active:
                x, y = randint(0, window_width), randint(-200, -100)
                Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and not game_active:
                    reset_game()
                if event.key == pygame.K_ESCAPE and not game_active:
                    running = False

        # Update the game state
        all_sprites.update(dt)
        
        # Collision handling
        if game_active:
            collision_handler()
                
        # Draw function
        screen.fill("#2e305e") 
        
        if game_active:
            display_score()
        else:
            display_game_over_screen()
            
        all_sprites.draw(screen)

        # flip() the display to put your work on screen
        pygame.display.update()
        await asyncio.sleep(0)
        
asyncio.run(main())
pygame.quit()