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

class MediaControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Media Control")
        self.attributes("-toolwindow", True)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.withdraw()

        self.frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#121212", border_width=1, border_color="#333333")
        self.frame.pack(padx=5, pady=5, fill="both", expand=True)

        self.source_label = ctk.CTkLabel(self.frame, text="", font=("Segoe UI", 10, "bold"), text_color="#1DB954")
        self.source_label.pack(pady=(10, 0))

        self.title_label = ctk.CTkLabel(self.frame, text="No Media", font=("Segoe UI", 13, "bold"))
        self.title_label.pack(pady=(2, 0), padx=10)
        
        self.artist_label = ctk.CTkLabel(self.frame, text="Waiting...", font=("Segoe UI", 11), text_color="#888888")
        self.artist_label.pack(pady=(0, 5))

        ctrl_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        ctrl_row.pack(pady=10)

        self.shuf_btn = ctk.CTkButton(ctrl_row, text="🔀", width=30, fg_color="transparent", command=lambda: self.media_cmd("shuffle"))
        self.shuf_btn.pack(side="left", padx=2)

        ctk.CTkButton(ctrl_row, text="⏮", width=30, fg_color="transparent", command=lambda: self.media_cmd("prev")).pack(side="left", padx=2)
        self.play_btn = ctk.CTkButton(ctrl_row, text="⏯", width=45, fg_color="#1DB954", text_color="#000000", command=lambda: self.media_cmd("play_pause"))
        self.play_btn.pack(side="left", padx=5)
        ctk.CTkButton(ctrl_row, text="⏭", width=30, fg_color="transparent", command=lambda: self.media_cmd("next")).pack(side="left", padx=2)

        self.rep_btn = ctk.CTkButton(ctrl_row, text="🔁", width=30, fg_color="transparent", command=lambda: self.media_cmd("repeat"))
        self.rep_btn.pack(side="left", padx=2)

        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        self.trigger.attributes("-toolwindow", True)

        tw, th = 8, 40
        self.trigger.geometry(f"{tw}x{th}+{self.winfo_screenwidth()-tw}+{self.winfo_screenheight()//2-(th//2)}")
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
                
                self.title_label.configure(text=props.title[:25] if props.title else "Unknown")
                self.artist_label.configure(text=props.artist[:30] if props.artist else "Unknown Artist")

                raw_source = session.source_app_user_model_id.split('!')[0].split('\\')[-1].upper()
                self.source_label.configure(text=f"• {raw_source}")

                self.shuf_btn.configure(text_color="#1DB954" if timeline.is_shuffle_active else "white")
                self.rep_btn.configure(text_color="#1DB954" if timeline.auto_repeat_mode > 0 else "white")
        except: pass

    def update_loop(self):
        while True:
            asyncio.run(self._update_ui())
            import time
            time.sleep(1.5)

    def show_player(self, e):
        w, h = 240, 150
        x, y = self.winfo_screenwidth() - w - 10, self.winfo_screenheight() // 2 - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()

    def hide_player(self, e):
        self.after(500, self._check_mouse_pos)

    def _check_mouse_pos(self):
        x, y = self.winfo_pointerxy()
        if not (self.winfo_x() <= x <= self.winfo_x() + self.winfo_width()):
            self.withdraw()

    def media_cmd(self, action):
        async def cmd():
            try:
                m = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
                s = m.get_current_session()
                if s:
                    if action == "play_pause": await s.try_toggle_play_pause_async()
                    elif action == "next": await s.try_skip_next_async()
                    elif action == "prev": await s.try_skip_previous_async()
                    elif action == "shuffle": await s.try_change_shuffle_active_async(not s.get_timeline_properties().is_shuffle_active)
                    elif action == "repeat":
                        cur = s.get_timeline_properties().auto_repeat_mode
                        await s.try_change_auto_repeat_mode_async(1 if cur == 0 else 0)
            except: pass
        threading.Thread(target=lambda: asyncio.run(cmd())).start()

if __name__ == "__main__":
    app = MediaControlApp()
    app.mainloop()
