import customtkinter as ctk
import time
import os
import threading
import sys
import ctypes
import winshell
from pywin32 import winsound

class MediaControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Media Control")
        self.attributes("-topmost", True)
        self.overrideredirect(True) 
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.withdraw()

        self.geometry("260x170")
        
        self.frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212", border_width=1, border_color="#333")
        self.frame.pack(padx=5, pady=5, fill="both", expand=True)

        left_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(15, 0))

        self.title_label = ctk.CTkLabel(left_frame, text="Artist", font=("Segoe UI", 16, "bold"), text_color="white", anchor="w")
        self.title_label.pack(fill="x", pady=(20, 0))
        
        self.source_label = ctk.CTkLabel(left_frame, text="Source", font=("Segoe UI", 12), text_color="#aaaaaa", anchor="w")
        self.source_label.pack(fill="x")

        ctrl_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=(15, 0))
        
        ctk.CTkButton(ctrl_frame, text="⏮", font=("Arial", 16), width=35, height=35, fg_color="transparent", hover_color="#333", command=lambda: self._simulate_media_key(0xB1)).pack(side="left", padx=5)
        
        self.play_btn = ctk.CTkButton(ctrl_frame, text="⏯", font=("Arial", 18), width=50, height=35, fg_color="#1DB954", text_color="black", hover_color="#26e068", command=lambda: self._simulate_media_key(0xB3))
        self.play_btn.pack(side="left", padx=5)
        

        ctk.CTkButton(ctrl_frame, text="⏭", font=("Arial", 16), width=35, height=35, fg_color="transparent", hover_color="#333", command=lambda: self._simulate_media_key(0xB0)).pack(side="left", padx=5)


        vol_frame = ctk.CTkFrame(self.frame, width=50, fg_color="#222", corner_radius=10)
        vol_frame.pack(side="right", fill="y", padx=10, pady=10)

        ctk.CTkLabel(vol_frame, text="🔊", text_color="#aaaaaa", font=("Segoe UI", 16)).pack(pady=(10, 5))
        
        self.vol_slider = ctk.CTkSlider(vol_frame, from_=0, to=100, orientation="vertical", width=18, height=100, fg_color="#444", progress_color="#888", button_color="#1DB954", button_hover_color="#26e068", command=self._set_volume)
        self.vol_slider.pack(pady=5)
        
        self.vol_label = ctk.CTkLabel(vol_frame, text="--%", text_color="#aaaaaa", font=("Segoe UI", 10))
        self.vol_label.pack(pady=(0, 10))

        self.start_btn = ctk.CTkButton(self.frame, text="⚙️ Startup", width=60, height=20, font=("Segoe UI", 9), fg_color="#222", text_color="white", corner_radius=5, command=self.add_to_startup)
        self.start_btn.place(relx=0.07, rely=0.82)


        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        self.trigger.attributes("-transparentcolor", "black")
        self.trigger.config(bg='black')


        r = 25
        self.trigger.geometry(f"{r}x{r*2}+{self.winfo_screenwidth()-1}+{self.winfo_screenheight()//2-r}")

        self.arc = ctk.CTkFrame(self.trigger, width=r*2, height=r*2, corner_radius=r, fg_color="#1DB954")
        self.arc.place(x=-r, y=0)

        self.trigger.bind("<Enter>", self.show_player)
        self.bind("<Leave>", self.hide_player)

        self.after(2000, self.update_volume_and_info)


    def show_player(self, e):
        self.update_volume_and_info(True)
        x = self.trigger.winfo_x() - 275
        y = self.trigger.winfo_y() + (self.trigger.winfo_height()//2) - (self.winfo_height()//2)
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide_player(self, e):
        self.after(100, self._check_mouse_pos)

    def _check_mouse_pos(self):
        x, y = self.winfo_pointerxy()
        if not (self.winfo_x() <= x <= self.winfo_x() + self.winfo_width()):
            self.withdraw()

    def update_volume_and_info(self, force_update=False):
        try:
            vol = ctypes.c_int()
            ctypes.windll.winmm.waveOutGetVolume(0, ctypes.byref(vol))
            current_volume = (vol.value & 0xFFFF) // 655
            self.vol_slider.set(current_volume)
            self.vol_label.configure(text=f"{current_volume}%")
        except: pass

        self.title_label.configure(text="Track Title")
        self.source_label.configure(text="Source Application")

        if not force_update:
            self.after(2000, self.update_volume_and_info)

    def _set_volume(self, value):
        new_vol_scaled = int(value * 655.35)
        vol_hex = (new_vol_scaled & 0xFFFF) | (new_vol_scaled << 16)
        ctypes.windll.winmm.waveOutSetVolume(0, vol_hex)
        self.vol_label.configure(text=f"{int(value)}%")

    def _simulate_media_key(self, vkey):
        ctypes.windll.user32.keybd_event(vkey, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vkey, 0, 2, 0)

    def add_to_startup(self):
        file_path = sys.executable if getattr(sys, 'frozen', False) else os.path.realpath(__file__)
        startup_path = os.path.join(winshell.startup(), "MediaControl.lnk")
        try:
            with winshell.shortcut(startup_path) as shortcut:
                shortcut.path = file_path
                shortcut.description = "Media Control"
            ctypes.windll.user32.MessageBoxW(0, "Startup enabled!", "Media Control", 0x40)
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, f"Error: {e}", "Media Control", 0x10)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = MediaControlApp()
    app.mainloop()
