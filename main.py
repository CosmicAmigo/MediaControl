import customtkinter as ctk
import asyncio
import threading
import io
import os
import sys
import ctypes
import winshell
from PIL import Image

# Use winsdk instead of winrt for better stability in compiled EXEs
import winsdk.windows.media.control as wmc
import winsdk.windows.storage.streams as wss

class MediaControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Media Control")
        self.overrideredirect(True)  # Frameless for that clean UI look
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.withdraw() # Start hidden until hover

        # --- UI Layout ---
        self.frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212", border_width=1, border_color="#333")
        self.frame.pack(padx=5, pady=5, fill="both", expand=True)

        # Album Art (Right Side)
        self.art_label = ctk.CTkLabel(self.frame, text="💿", width=80, height=80, fg_color="#222", corner_radius=8)
        self.art_label.grid(row=0, column=2, rowspan=2, padx=15, pady=15)

        # Song Info
        self.title_label = ctk.CTkLabel(self.frame, text="No Media", font=("Segoe UI", 15, "bold"), anchor="w")
        self.title_label.grid(row=0, column=0, columnspan=2, padx=(15, 0), sticky="w", pady=(15, 0))
        
        self.artist_label = ctk.CTkLabel(self.frame, text="Waiting...", font=("Segoe UI", 11), text_color="#888", anchor="w")
        self.artist_label.grid(row=1, column=0, columnspan=2, padx=(15, 0), sticky="nw")

        # Control Buttons
        btn_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_f.grid(row=2, column=0, columnspan=2, pady=(0, 10), padx=10)
        
        ctk.CTkButton(btn_f, text="⏮", width=35, fg_color="transparent", hover_color="#333", command=lambda: self.run_async("prev")).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="⏯", width=45, fg_color="#1DB954", text_color="white", command=lambda: self.run_async("play_pause")).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="⏭", width=35, fg_color="transparent", hover_color="#333", command=lambda: self.run_async("next")).pack(side="left", padx=5)

        # Startup Button
        self.start_btn = ctk.CTkButton(self.frame, text="⚙️ Startup", width=60, height=20, font=("Segoe UI", 9), fg_color="#222", command=self.add_to_startup)
        self.start_btn.grid(row=2, column=2, pady=(0, 10))

        # --- The Trigger Strip ---
        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        # Position strip on far right edge
        self.trigger.geometry(f"5x120+{self.winfo_screenwidth()-5}+{self.winfo_screenheight()//2-60}")
        self.trigger.configure(fg_color="#1DB954") 
        
        self.trigger.bind("<Enter>", self.show_player)
        self.bind("<Leave>", self.hide_player)

        threading.Thread(target=self.update_loop, daemon=True).start()

    # --- Media Info Logic (Winsdk) ---
    async def get_art(self, session):
        try:
            props = await session.try_get_media_properties_async()
            if not props.thumbnail: return None
            
            stream = await props.thumbnail.open_read_async()
            reader = wss.DataLoader(stream)
            await reader.load_async(stream.size)
            buffer = reader.read_buffer(stream.size)
            
            # Memory mapping for thumbnail
            addr = ctypes.addressof(ctypes.c_char.from_buffer(buffer))
            data = ctypes.string_at(addr, buffer.length)
            
            img = Image.open(io.BytesIO(data))
            return ctk.CTkImage(img, size=(80, 80))
        except: return None

    async def _update_ui(self):
        try:
            manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            session = manager.get_current_session()
            if session:
                props = await session.try_get_media_properties_async()
                self.title_label.configure(text=(props.title[:20] if props.title else "Unknown"))
                self.artist_label.configure(text=(props.artist[:25] if props.artist else "Unknown Artist"))
                
                art = await self.get_art(session)
                if art: self.art_label.configure(image=art, text="")
        except: pass

    def update_loop(self):
        while True:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._update_ui())
            loop.close()
            import time
            time.sleep(2)

    # --- Interaction Logic ---
    def show_player(self, e):
        w, h = 340, 170
        x = self.winfo_screenwidth() - w - 10
        y = self.winfo_screenheight() // 2 - (h // 2)
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
        threading.Thread(target=lambda: asyncio.run(cmd())).start()

    def add_to_startup(self):
        file_path = sys.executable if getattr(sys, 'frozen', False) else os.path.realpath(__file__)
        startup_path = os.path.join(winshell.startup(), "MediaControl.lnk")
        try:
            with winshell.shortcut(startup_path) as shortcut:
                shortcut.path = file_path
                shortcut.description = "Media Control"
            ctypes.windll.user32.MessageBoxW(0, "Success!", "Media Control", 0x40)
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, f"Error: {e}", "Media Control", 0x10)

if __name__ == "__main__":
    app = MediaControlApp()
    app.mainloop()
