import customtkinter as ctk
import asyncio
import threading
import os
import sys
import ctypes
import winshell
from PIL import Image
import winsdk.windows.media.control as wmc

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MiniMediaControl(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Media Control")
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
            
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

        self.title_label = ctk.CTkLabel(self.frame, text="No Media", font=("Segoe UI", 12, "bold"))
        self.title_label.pack(pady=(2, 0), padx=10)
        
        self.artist_label = ctk.CTkLabel(self.frame, text="Waiting...", font=("Segoe UI", 10), text_color="#888")
        self.artist_label.pack(pady=(0, 5))

        # --- Load Icons ---
        try:
            self.img_prev = ctk.CTkImage(Image.open(resource_path("prev.png")), size=(20, 20))
            self.img_play = ctk.CTkImage(Image.open(resource_path("play.png")), size=(25, 25))
            self.img_next = ctk.CTkImage(Image.open(resource_path("next.png")), size=(20, 20))
            self.img_shuf = ctk.CTkImage(Image.open(resource_path("shuffle.png")), size=(18, 18))
            self.img_rep  = ctk.CTkImage(Image.open(resource_path("repeat.png")), size=(18, 18))
        except:
            self.img_prev = self.img_play = self.img_next = self.img_shuf = self.img_rep = None

        # Main Controls (Prev, Play, Next)
        ctrl_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        ctrl_frame.pack(pady=5)
        
        ctk.CTkButton(ctrl_frame, text="" if self.img_prev else "⏮", image=self.img_prev, width=30, fg_color="transparent", hover_color="#333", command=lambda: self.run_async("prev")).pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(ctrl_frame, text="" if self.img_play else "⏯", image=self.img_play, width=45, fg_color="#1DB954", command=lambda: self.run_async("play_pause"))
        self.play_btn.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="" if self.img_next else "⏭", image=self.img_next, width=30, fg_color="transparent", hover_color="#333", command=lambda: self.run_async("next")).pack(side="left", padx=5)

        # Toggle Controls (Shuffle, Repeat)
        toggle_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        toggle_frame.pack(pady=(0, 10))

        self.shuffle_btn = ctk.CTkButton(toggle_frame, text="" if self.img_shuf else "🔀", image=self.img_shuf, width=25, fg_color="transparent", hover_color="#222", command=lambda: self.run_async("shuffle"))
        self.shuffle_btn.pack(side="left", padx=15)
        
        self.repeat_btn = ctk.CTkButton(toggle_frame, text="" if self.img_rep else "🔁", image=self.img_rep, width=25, fg_color="transparent", hover_color="#222", command=lambda: self.run_async("repeat"))
        self.repeat_btn.pack(side="left", padx=15)

        # Trigger Strip
        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        self.trigger.geometry(f"5x80+{self.winfo_screenwidth()-5}+{self.winfo_screenheight()//2-40}")
        self.trigger.configure(fg_color="#1DB954") 
        self.trigger.bind("<Enter>", self.show_player)
        self.bind("<Leave>", self.hide_player)

        threading.Thread(target=self.update_loop, daemon=True).start()

    async def _update_ui(self):
        try:
            manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            session = manager.get_current_session()
            if session:
                props = await session.try_get_media_properties_async()
                timeline = session.get_timeline_properties()
                
                # Update Info
                self.title_label.configure(text=props.title[:22] if props.title else "Unknown")
                self.artist_label.configure(text=props.artist[:25] if props.artist else "Unknown Artist")
                source = session.source_app_user_model_id.split('!')[0].split('.')[-1].upper()
                self.source_label.configure(text=f"• {source} •")

                # Update Shuffle Color (Green if active)
                if timeline.is_shuffle_active:
                    self.shuffle_btn.configure(text_color="#1DB954", fg_color="#1a2e1f")
                else:
                    self.shuffle_btn.configure(text_color="white", fg_color="transparent")

                # Update Repeat Color (Green if active)
                # Mode 0 = Off, 1 = List, 2 = Single Track
                if timeline.auto_repeat_mode is not None and timeline.auto_repeat_mode > 0:
                    self.repeat_btn.configure(text_color="#1DB954", fg_color="#1a2e1f")
                else:
                    self.repeat_btn.configure(text_color="white", fg_color="transparent")
        except: pass

    def update_loop(self):
        while True:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._update_ui())
            loop.close()
            import time
            time.sleep(1.5)

    def show_player(self, e):
        w, h = 220, 170
        x, y = self.winfo_screenwidth() - w - 10, self.winfo_screenheight() // 2 - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()

    def hide_player(self, e):
        self.after(500, self._check_mouse_pos)

    def _check_mouse_pos(self):
        x, y = self.winfo_pointerxy()
        if not (self.winfo_x() <= x <= self.winfo_x() + self.winfo_width()):
            self.withdraw()

    def run_async(self, action):
        async def cmd():
            m = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            s = m.get_current_session()
            if s:
                if action == "play_pause": await s.try_toggle_play_pause_async()
                elif action == "next": await s.try_skip_next_async()
                elif action == "prev": await s.try_skip_previous_async()
                elif action == "shuffle":
                    timeline = s.get_timeline_properties()
                    await s.try_change_shuffle_active_async(not timeline.is_shuffle_active)
                elif action == "repeat":
                    timeline = s.get_timeline_properties()
                    # Toggles between Mode 0 (Off) and Mode 1 (Repeat List)
                    new_mode = 1 if timeline.auto_repeat_mode == 0 else 0
                    await s.try_change_auto_repeat_mode_async(new_mode)
        threading.Thread(target=lambda: asyncio.run(cmd())).start()

if __name__ == "__main__":
    app = MiniMediaControl()
    app.mainloop()
