import cv2
import mediapipe as mp
import numpy as np
import pygame
import random
import time
import threading
import os

# -------------------------------
# Initialize pygame mixer
# -------------------------------
pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# -------------------------------
# Load sounds
# -------------------------------
def load_sound(name):
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

sound_eat = load_sound("eat_point.mp3")
sound_over = load_sound("game_over.mp3")
sound_tick = load_sound("countdown_beep.mp3")
bg_music = os.path.join(ASSETS_DIR, "game_bg_music.mp3")

# -------------------------------
# Gesture Controller
# -------------------------------
class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.direction = "RIGHT"
        self.prev_pos = None
        self.cooldown = 0
        self.max_cooldown = 8
        self.gesture_threshold = 0.05
        self.is_fist = False

    def detect_gesture(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)
        direction = None
        is_pinching = False
        self.is_fist = False

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )

                # wrist movement
                wrist = hand.landmark[self.mp_hands.HandLandmark.WRIST]
                cur_pos = np.array([wrist.x, wrist.y])
                if self.prev_pos is not None and self.cooldown <= 0:
                    movement = cur_pos - self.prev_pos
                    if np.linalg.norm(movement) > self.gesture_threshold:
                        if abs(movement[0]) > abs(movement[1]):
                            direction = "RIGHT" if movement[0] > 0 else "LEFT"
                        else:
                            direction = "DOWN" if movement[1] > 0 else "UP"
                        self.direction = direction
                        self.cooldown = self.max_cooldown
                self.prev_pos = cur_pos

                # Detect pinch
                thumb_tip = hand.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                dist = np.linalg.norm(np.array([thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y]))
                is_pinching = dist < 0.05

                # Detect fist
                tips = [
                    self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
                    self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                    self.mp_hands.HandLandmark.RING_FINGER_TIP,
                    self.mp_hands.HandLandmark.PINKY_TIP
                ]
                mcps = [
                    self.mp_hands.HandLandmark.INDEX_FINGER_MCP,
                    self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
                    self.mp_hands.HandLandmark.RING_FINGER_MCP,
                    self.mp_hands.HandLandmark.PINKY_MCP
                ]
                folded = 0
                for t, m in zip(tips, mcps):
                    if hand.landmark[t].y > hand.landmark[m].y:
                        folded += 1
                if folded >= 4:
                    self.is_fist = True

        if self.cooldown > 0:
            self.cooldown -= 1

        return self.direction, is_pinching, frame, self.is_fist


# -------------------------------
# Snake Game Class
# -------------------------------
CELL_SIZE = 20

class SnakeGame:
    def __init__(self):
        os.environ['SDL_VIDEO_WINDOW_POS'] = "700,150"
        pygame.init()
        self.width, self.height = 600, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("🐍 Gesture Snake Game")
        self.clock = pygame.time.Clock()
        self.running = True

        self.BLACK = (10, 10, 10)
        self.GREEN = (50, 205, 50)
        self.RED = (255, 80, 80)
        self.WHITE = (255, 255, 255)

        self.snake = [(200, 200), (180, 200), (160, 200)]
        self.direction = "RIGHT"
        self.score = 0
        self.food = self.spawn_food()
        self.active = False
        self.countdown_done = False

        if os.path.exists(bg_music):
            pygame.mixer.music.load(bg_music)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)

    def spawn_food(self):
        x = random.randint(0, (self.width - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        y = random.randint(0, (self.height - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        return (x, y)

    def move(self, boost=False):
        if not self.active or not self.countdown_done:
            return
        x, y = self.snake[0]
        if self.direction == "UP": y -= CELL_SIZE
        elif self.direction == "DOWN": y += CELL_SIZE
        elif self.direction == "LEFT": x -= CELL_SIZE
        elif self.direction == "RIGHT": x += CELL_SIZE

        new_head = (x, y)
        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            if sound_eat: sound_eat.play()
            self.food = self.spawn_food()
        else:
            self.snake.pop()

        if x < 0 or x >= self.width or y < 0 or y >= self.height or new_head in self.snake[1:]:
            self.running = False
            if sound_over: sound_over.play()

    def draw(self, message=""):
        self.screen.fill(self.BLACK)
        for x, y in self.snake:
            pygame.draw.rect(self.screen, self.GREEN, (x, y, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(self.screen, self.RED, (*self.food, CELL_SIZE, CELL_SIZE))
        font = pygame.font.SysFont("Poppins", 26)
        text = font.render(f"Score: {self.score}", True, self.WHITE)
        self.screen.blit(text, (10, 10))
        if message:
            msg_font = pygame.font.SysFont("Poppins", 34, bold=True)
            msg_render = msg_font.render(message, True, (255, 255, 0))
            rect = msg_render.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(msg_render, rect)
        pygame.display.flip()

    def countdown(self):
        font = pygame.font.SysFont("Poppins", 120, bold=True)
        for i in range(5, 0, -1):
            self.draw(str(i))
            if sound_tick: sound_tick.play()
            pygame.display.flip()
            pygame.time.wait(1000)
        self.countdown_done = True
        self.active = True

    def quit(self):
        pygame.mixer.music.stop()
        pygame.quit()


# -------------------------------
# Combined System
# -------------------------------
def run_gesture_game():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not access webcam.")
        return

    controller = GestureController()
    game = SnakeGame()

    cv2.namedWindow("✋ Gesture Control (Webcam)")
    cv2.moveWindow("✋ Gesture Control (Webcam)", 50, 150)

    print("🖐 Game ready — show fist ✊ to start countdown.")

    countdown_thread = None

    while game.running:
        # ----- Camera Feed -----
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        gesture, pinch, annotated, is_fist = controller.detect_gesture(frame)

        # Game trigger
        if is_fist and not game.countdown_done:
            if countdown_thread is None or not countdown_thread.is_alive():
                print("✊ Fist detected — starting countdown!")
                countdown_thread = threading.Thread(target=game.countdown)
                countdown_thread.start()

        # Normal movement
        if gesture:
            game.direction = gesture
        game.move(boost=pinch)
        game.draw("" if game.countdown_done else "Show Fist ✊ to Start")

        # Annotate webcam feed
        cv2.putText(annotated, f"Gesture: {gesture}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 3)
        if is_fist:
            cv2.putText(annotated, "FIST DETECTED ✊", (30, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        cv2.imshow("✋ Gesture Control (Webcam)", annotated)

        # Control FPS for smoothness
        game.clock.tick(10)

        key = cv2.waitKey(1) & 0xFF
        if key in [27, ord('q')]:
            game.running = False
            break

    # Cleanup
    game.quit()
    cap.release()
    cv2.destroyAllWindows()
    print("👋 Game closed safely.")


if __name__ == "__main__":
    run_gesture_game()
