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

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.withdraw()

        self.frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212", border_width=1, border_color="#333333")
        self.frame.pack(padx=5, pady=5, fill="both", expand=True)

        self.info_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.info_frame.pack(side="left", fill="both", expand=True, padx=15)

        self.source_label = ctk.CTkLabel(self.info_frame, text="", font=("Segoe UI", 10, "bold"), text_color="#1DB954")
        self.source_label.pack(pady=(15, 0), anchor="w")

        self.title_label = ctk.CTkLabel(self.info_frame, text="No Media", font=("Segoe UI", 14, "bold"), anchor="w")
        self.title_label.pack(fill="x", pady=(2, 0))
        
        self.artist_label = ctk.CTkLabel(self.info_frame, text="Waiting...", font=("Segoe UI", 11), text_color="#888888", anchor="w")
        self.artist_label.pack(fill="x")

        ctrl_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        ctrl_frame.pack(pady=15, anchor="w")
        
        ctk.CTkButton(ctrl_frame, text="⏮", width=30, fg_color="transparent", command=lambda: self.media_cmd("prev")).pack(side="left")
        self.play_btn = ctk.CTkButton(ctrl_frame, text="⏯", width=45, fg_color="#1DB954", text_color="#000000", command=lambda: self.media_cmd("play_pause"))
        self.play_btn.pack(side="left", padx=10)
        ctk.CTkButton(ctrl_frame, text="⏭", width=30, fg_color="transparent", command=lambda: self.media_cmd("next")).pack(side="left")

        self.vol_frame = ctk.CTkFrame(self.frame, fg_color="#1A1A1A", corner_radius=10, width=40)
        self.vol_frame.pack(side="right", fill="y", padx=(0, 10), pady=10)

        self.vol_slider = ctk.CTkSlider(self.vol_frame, from_=0, to=100, orientation="vertical", width=16, 
                                        button_color="#1DB954", progress_color="#1DB954", command=self.set_volume)
        self.vol_slider.pack(expand=True, pady=10)

        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        self.trigger.attributes("-transparentcolor", "black")
        self.trigger.config(bg='black')
        
        r = 25
        self.trigger.geometry(f"{r}x{r*2}+{self.winfo_screenwidth()-1}+{self.winfo_screenheight()//2-r}")

        self.visual_trigger = ctk.CTkFrame(self.trigger, width=r*2, height=r*2, corner_radius=r, fg_color="#1DB954")
        self.visual_trigger.place(x=0, y=0) 

        self.trigger.bind("<Enter>", self.show_player)
        self.bind("<Leave>", self.hide_player)

        threading.Thread(target=self.update_loop, daemon=True).start()

    def set_volume(self, val):
        try:
            v = int(val * 655.35)
            ctypes.windll.winmm.waveOutSetVolume(0, (v & 0xFFFF) | (v << 16))
        except: pass

    def get_sys_volume(self):
        try:
            v = ctypes.c_int()
            ctypes.windll.winmm.waveOutGetVolume(0, ctypes.byref(v))
            return (v.value & 0xFFFF) // 655
        except: return 50

    async def _update_ui(self):
        try:
            manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            session = manager.get_current_session()
            self.vol_slider.set(self.get_sys_volume())
            if session:
                props = await session.try_get_media_properties_async()
                self.title_label.configure(text=props.title[:25] if props.title else "Unknown")
                self.artist_label.configure(text=props.artist[:30] if props.artist else "Unknown Artist")
                source = session.source_app_user_model_id.split('!')[0].split('.')[-1].upper()
                self.source_label.configure(text=f"• {source}")
        except: pass

    def update_loop(self):
        while True:
            asyncio.run(self._update_ui())
            import time
            time.sleep(2)

    def show_player(self, e):
        w, h = 320, 160
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
            except: pass
        threading.Thread(target=lambda: asyncio.run(cmd())).start()

if __name__ == "__main__":
    app = MediaControlApp()
    app.mainloop()
