import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageSequence
import threading
import pygame
import os
import subprocess
import sys

# ----------------------------
# Initialize pygame mixer
# ----------------------------
pygame.mixer.init()

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ----------------------------
# Music Control
# ----------------------------
def play_music():
    """Play looping intro music"""
    try:
        music_path = os.path.join(ASSETS_DIR, "start_music.mp3")
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)
    except Exception as e:
        print("Music Error:", e)

def stop_music():
    """Stop music before game launch"""
    pygame.mixer.music.stop()


# ----------------------------
# Home Screen Class
# ----------------------------
class SnakeGameHome(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🐍 Modern Snake Game")
        self.geometry("800x600")
        self.resizable(False, False)
        self.eval('tk::PlaceWindow . center')
        self.configure(bg="#0b132b")

        # Background Animation
        self.bg_label = tk.Label(self, bg="#0b132b")
        self.bg_label.pack(fill="both", expand=True)
        self.animate_background()

        # Bottom-right control panel
        self.bottom_panel = tk.Frame(self, bg="#0a0f15", highlightthickness=0, bd=0)
        self.bottom_panel.place(relx=0.98, rely=0.95, anchor="se")

        self.button_frame = tk.Frame(self.bottom_panel, bg="#081826", highlightthickness=0, bd=0)
        self.button_frame.pack(padx=20, pady=15)

        # Create buttons
        self.play_manual_btn = self.create_modern_button("🎮  Play Manually", self.play_manual)
        self.play_gesture_btn = self.create_modern_button("✋  Play Using Gestures", self.play_gesture)
        self.scoreboard_btn = self.create_modern_button("🏆  Scoreboard", self.show_scoreboard)
        self.about_btn = self.create_modern_button("ℹ️  About", self.show_about)
        self.exit_btn = self.create_modern_button("❌  Exit", self.quit_game)

        self.play_manual_btn.pack(anchor="w", padx=20, pady=5)
        self.play_gesture_btn.pack(anchor="w", padx=20, pady=5)
        self.scoreboard_btn.pack(anchor="w", padx=20, pady=5)
        self.about_btn.pack(anchor="w", padx=20, pady=5)
        self.exit_btn.pack(anchor="w", padx=20, pady=5)

        # Start background music in a separate thread
        threading.Thread(target=play_music, daemon=True).start()

    # ----------------------------
    # Background Animation
    # ----------------------------
    def animate_background(self):
        gif_path = os.path.join(ASSETS_DIR, "bg_animation.gif")
        if not os.path.exists(gif_path):
            self.bg_label.config(bg="#1a1a1a")
            return

        frames = []
        for img in ImageSequence.Iterator(Image.open(gif_path)):
            img_ratio = img.width / img.height
            target_ratio = 800 / 600
            if img_ratio > target_ratio:
                new_height = 600
                new_width = int(new_height * img_ratio)
            else:
                new_width = 800
                new_height = int(new_width / img_ratio)
            resized = img.resize((new_width, new_height), Image.LANCZOS)
            # Crop center
            left = (resized.width - 800) // 2
            top = (resized.height - 600) // 2
            cropped = resized.crop((left, top, left + 800, top + 600))
            frames.append(ImageTk.PhotoImage(cropped))
        self.frames = frames

        def update_frame(index=0):
            frame = self.frames[index]
            self.bg_label.configure(image=frame)
            index = (index + 1) % len(self.frames)
            self.after(60, update_frame, index)

        update_frame()

    # ----------------------------
    # Modern Button Creator
    # ----------------------------
    def create_modern_button(self, text, command):
        btn = tk.Button(
            self.button_frame,
            text=text,
            font=("Poppins", 14, "bold"),
            fg="#66ffcc",
            bg="#081826",
            activeforeground="#ffcc00",
            activebackground="#081826",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=command
        )

        def on_enter(e): btn.config(fg="#ffcc00", cursor="hand2")
        def on_leave(e): btn.config(fg="#66ffcc", cursor="arrow")
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # ----------------------------
    # Button Actions
    # ----------------------------
    def play_manual(self):
        stop_music()
        self.destroy()
        print("🎮 Launching Manual Mode...")
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "manual_snake_game.py")])
        os.execl(sys.executable, sys.executable, *sys.argv)  # Relaunch main menu

    def play_gesture(self):
        stop_music()
        self.destroy()
        print("✋ Launching Gesture Mode...")
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "gesture_snake_game.py")])
        os.execl(sys.executable, sys.executable, *sys.argv)

    def show_scoreboard(self):
        score_file = os.path.join(BASE_DIR, "scores.txt")
        if not os.path.exists(score_file):
            messagebox.showinfo("Scoreboard", "No scores recorded yet.")
            return

        with open(score_file, "r") as f:
            scores = f.read().strip()
        messagebox.showinfo("🏆 Scoreboard", scores or "No scores available.")

    def show_about(self):
        about_text = (
            "🐍 Modern Snake Game\n\n"
            "Developed by: Narendra Mishra\n"
            "B.Tech CSIT, 2nd Year\n\n"
            "Technologies:\n"
            "- Python\n"
            "- Tkinter GUI\n"
            "- Pygame (Game Engine)\n"
            "- OpenCV + MediaPipe (AI Gesture Control)\n\n"
            "© 2025 Project Work"
        )
        messagebox.showinfo("About", about_text)

    def quit_game(self):
        stop_music()
        self.destroy()


# ----------------------------
# Run the App
# ----------------------------
if __name__ == "__main__":
    app = SnakeGameHome()
    app.mainloop()
