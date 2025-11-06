import pygame
import random
import os
import subprocess
import sys

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Screen setup
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CELL_SIZE = 20
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🐍 Snake Game - Manual Mode")

# Colors
BLACK = (10, 15, 21)
GREEN = (102, 255, 204)
LIGHT_GREEN = (0, 255, 170)
YELLOW = (255, 204, 0)
RED = (255, 80, 80)
WHITE = (255, 255, 255)
GRID_COLOR = (25, 35, 45)

# Fonts
font = pygame.font.SysFont("Poppins", 28, bold=True)
small_font = pygame.font.SysFont("Poppins", 22)
big_font = pygame.font.SysFont("Poppins", 60, bold=True)

# Load Sounds
def load_sound(file):
    path = os.path.join(ASSETS_DIR, file)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

sound_start = load_sound("game_start.mp3")
sound_eat = load_sound("eat_point.mp3")
sound_over = load_sound("game_over.mp3")

bg_music_path = os.path.join(ASSETS_DIR, "game_bg_music.mp3")

# Snake Game Class
class SnakeGame:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.speed = 8

        # Snake setup
        self.snake = [(100, 50), (90, 50), (80, 50)]
        self.direction = "RIGHT"

        # Food setup
        self.food = self.spawn_food()
        self.score = 0

        # Play start sound
        if sound_start:
            sound_start.play()
        
        # Background Music
        if os.path.exists(bg_music_path):
            pygame.mixer.music.load(bg_music_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)

    def spawn_food(self):
        return (
            random.randrange(0, (SCREEN_WIDTH // CELL_SIZE)) * CELL_SIZE,
            random.randrange(0, (SCREEN_HEIGHT // CELL_SIZE)) * CELL_SIZE
        )

    def move(self):
        x, y = self.snake[0]

        # move in grid steps
        if self.direction == "UP":
            y -= CELL_SIZE
        elif self.direction == "DOWN":
            y += CELL_SIZE
        elif self.direction == "LEFT":
            x -= CELL_SIZE
        elif self.direction == "RIGHT":
            x += CELL_SIZE

    # round to nearest cell to prevent float mismatches
        x = (x // CELL_SIZE) * CELL_SIZE
        y = (y // CELL_SIZE) * CELL_SIZE

        new_head = (x, y)
        self.snake.insert(0, new_head)

    # Ensure food and snake positions are aligned to grid
        fx, fy = self.food
        fx = (fx // CELL_SIZE) * CELL_SIZE
        fy = (fy // CELL_SIZE) * CELL_SIZE

    # Correct food-eating detection
        if abs(new_head[0] - fx) < CELL_SIZE and abs(new_head[1] - fy) < CELL_SIZE:
            self.score += 10
            if sound_eat:
                sound_eat.play()
            self.food = self.spawn_food()
        else:
            self.snake.pop()


    def check_collision(self):
        head_x, head_y = self.snake[0]
        # Wall collision
        if (
            head_x < 0 or head_x >= SCREEN_WIDTH or
            head_y < 0 or head_y >= SCREEN_HEIGHT
        ):
            self.game_over = True
        # Self collision
        for block in self.snake[1:]:
            if (head_x, head_y) == block:
                self.game_over = True

    def draw_snake(self):
        for i, pos in enumerate(self.snake):
            color = LIGHT_GREEN if i == 0 else GREEN
            pygame.draw.rect(screen, color, pygame.Rect(pos[0], pos[1], CELL_SIZE - 1, CELL_SIZE - 1))

    def draw_food(self):
        pygame.draw.rect(screen, YELLOW, pygame.Rect(self.food[0], self.food[1], CELL_SIZE, CELL_SIZE))

    def draw_grid(self):
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and self.direction != "DOWN":
            self.direction = "UP"
        elif keys[pygame.K_DOWN] and self.direction != "UP":
            self.direction = "DOWN"
        elif keys[pygame.K_LEFT] and self.direction != "RIGHT":
            self.direction = "LEFT"
        elif keys[pygame.K_RIGHT] and self.direction != "LEFT":
            self.direction = "RIGHT"

    def draw_ui(self):
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

    def show_game_over(self):
        pygame.mixer.music.stop()
        if sound_over:
            sound_over.play()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        text_game_over = big_font.render("GAME OVER", True, YELLOW)
        text_score = font.render(f"Your Score: {self.score}", True, WHITE)
        text_restart = small_font.render("Press ENTER to Play Again", True, GREEN)
        text_back = small_font.render("Press ESC to Return to Home", True, RED)

        screen.blit(text_game_over, (SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT // 2 - 80))
        screen.blit(text_score, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        screen.blit(text_restart, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50))
        screen.blit(text_back, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 90))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        pygame.mixer.music.stop()
                        self.return_to_home()
                    if event.key == pygame.K_RETURN and self.game_over:
                        self.__init__()

            if not self.game_over:
                self.handle_input()
                self.move()
                self.check_collision()

                screen.fill(BLACK)
                self.draw_grid()
                self.draw_snake()
                self.draw_food()
                self.draw_ui()
            else:
                self.show_game_over()

            pygame.display.update()
            self.clock.tick(self.speed)

    def return_to_home(self):
        """Return to Tkinter home screen"""
        pygame.quit()
        python = sys.executable
        subprocess.Popen([python, os.path.join(BASE_DIR, "main_tkinter.py")])
        sys.exit()


# Run the game
if __name__ == "__main__":
    game = SnakeGame()
    game.run()
