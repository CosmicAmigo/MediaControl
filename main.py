import customtkinter as ctk
import asyncio
import threading
import os
import sys
import ctypes
import winshell
from PIL import Image
import winsdk.windows.media.control as wmc

# Helper to find images when bundled in EXE
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MiniMediaControl(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Media Control")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.withdraw()

        # --- UI Layout ---
        self.frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#121212", border_width=1, border_color="#333")
        self.frame.pack(padx=5, pady=5, fill="both", expand=True)

        self.source_label = ctk.CTkLabel(self.frame, text="", font=("Segoe UI", 9, "bold"), text_color="#1DB954")
        self.source_label.pack(pady=(8, 0))

        self.title_label = ctk.CTkLabel(self.frame, text="No Media", font=("Segoe UI", 13, "bold"))
        self.title_label.pack(pady=(2, 0), padx=10)
        
        self.artist_label = ctk.CTkLabel(self.frame, text="Waiting...", font=("Segoe UI", 10), text_color="#888")
        self.artist_label.pack(pady=(0, 5))

        # --- Load Icons ---
        # Note: You need to add these PNGs to your GitHub repo!
        try:
            self.img_prev = ctk.CTkImage(Image.open(resource_path("prev.png")), size=(20, 20))
            self.img_play = ctk.CTkImage(Image.open(resource_path("play.png")), size=(25, 25))
            self.img_next = ctk.CTkImage(Image.open(resource_path("next.png")), size=(20, 20))
        except:
            # Fallback to emojis if images are missing
            self.img_prev = self.img_play = self.img_next = None

        ctrl_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        ctrl_frame.pack(pady=5)
        
        ctk.CTkButton(ctrl_frame, text="" if self.img_prev else "⏮", image=self.img_prev, width=30, fg_color="transparent", command=lambda: self.run_async("prev")).pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(ctrl_frame, text="" if self.img_play else "⏯", image=self.img_play, width=45, fg_color="#1DB954", command=lambda: self.run_async("play_pause"))
        self.play_btn.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="" if self.img_next else "⏭", image=self.img_next, width=30, fg_color="transparent", command=lambda: self.run_async("next")).pack(side="left", padx=5)

        # Trigger Logic
        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        self.trigger.geometry(f"5x80+{self.winfo_screenwidth()-5}+{self.winfo_screenheight()//2-40}")
        self.trigger.configure(fg_color="#1DB954") 
        self.trigger.bind("<Enter>", self.show_player)
        self.bind("<Leave>", self.hide_player)

        threading.Thread(target=self.update_loop, daemon=True).start()

    # (Keep previous update_loop, show_player, hide_player, run_async, and add_to_startup functions here)
    # ... (rest of the logic from the previous message)

if __name__ == "__main__":
    app = MiniMediaControl()
    app.mainloop()
