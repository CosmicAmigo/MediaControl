import customtkinter as ctk
import asyncio
import threading
import io
import os
import sys
import ctypes
import winshell
from PIL import Image
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SessionManager
from winrt.windows.storage.streams import DataLoader

class MediaControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Media Control")
        self.overrideredirect(True)  # Frameless
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.withdraw() # Start hidden

        # --- UI Layout ---
        self.frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212", border_width=1, border_color="#333")
        self.frame.pack(padx=5, pady=5, fill="both", expand=True)

        # Album Art (Right Side)
        self.art_label = ctk.CTkLabel(self.frame, text="💿", width=80, height=80, fg_color="#222", corner_radius=8)
        self.art_label.grid(row=0, column=2, rowspan=2, padx=15, pady=15)

        # Song Info
        self.title_label = ctk.CTkLabel(self.frame, text="No Media", font=("Segoe UI", 15, "bold"), anchor="w")
        self.title_label.grid(row=0, column=0, columnspan=2, padx=(15, 0), sticky="w", pady=(15, 0))
        
        self.artist_label = ctk.CTkLabel(self.frame, text="Waiting for session...", font=("Segoe UI", 11), text_color="#888", anchor="w")
        self.artist_label.grid(row=1, column=0, columnspan=2, padx=(15, 0), sticky="nw")

        # Control Buttons
        btn_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_f.grid(row=2, column=0, columnspan=2, pady=(0, 10), padx=10)
        
        ctk.CTkButton(btn_f, text="⏮", width=35, fg_color="transparent", hover_color="#333", command=lambda: self.run_async("prev")).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="⏯", width=45, fg_color="#1DB954", text_color="white", command=lambda: self.run_async("play_pause")).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="⏭", width=35, fg_color="transparent", hover_color="#333", command=lambda: self.run_async("next")).pack(side="left", padx=5)

        # Startup Button (Bottom Right)
        self.start_btn = ctk.CTkButton(self.frame, text="⚙️ Startup", width=60, height=20, font=("Segoe UI", 9), fg_color="#222", command=self.add_to_startup)
        self.start_btn.grid(row=2, column=2, pady=(0, 10))

        # --- The Trigger Strip ---
        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        # Position a 5-pixel blue strip on the far right edge of the screen
        self.trigger.geometry(f"5x120+{self.winfo_screenwidth()-5}+{self.winfo_screenheight()//2-60}")
        self.trigger.configure(fg_color="#1DB954") 
        
        self.trigger.bind("<Enter>", self.show_player)
        self.bind("<Leave>", self.hide_player)

        # Start the update loop in a background thread
        threading.Thread(target=self.update_loop, daemon=True).start()

    # --- Media Logic ---
    async def get_art(self, session):
        try:
            props = await session.try_get_media_properties_async()
            if not props.thumbnail: return None
            
            stream = await props.thumbnail.open_read_async()
            reader = DataLoader(stream)
            await reader.load_async(stream.size)
            buffer = reader.read_buffer(stream.size)
            
            addr = ctypes.addressof(ctypes.c_char.from_buffer(buffer))
            data = ctypes.string_at(addr, buffer.length)
            
            img = Image.open(io.BytesIO(data))
            return ctk.CTkImage(img, size=(80, 80))
        except: return None

    async def _update_ui(self):
        try:
            sessions = await SessionManager.request_async()
            session = sessions.get_current_session()
            if session:
                props = await session.try_get_media_properties_async()
                self.title_label.configure(text=props.title[:20] if props.title else "Unknown")
                self.artist_label.configure(text=props.artist[:25] if props.artist else "Unknown Artist")
                
                art = await self.get_art(session)
                if art: self.art_label.configure(image=art, text="")
        except: pass

    def update_loop(self):
        while True:
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self._update_ui())
                loop.close()
            except: pass
            import time
            time.sleep(1.5)

    # --- Animation & Hover Logic ---
    def show_player(self, e):
        w, h = 340, 170
        x = self.winfo_screenwidth() - w - 10
        y = self.winfo_screenheight() // 2 - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()

    def hide_player(self, e):
        # Wait a split second and check if mouse is still not over the window
        self.after(500, self._check_mouse_pos)

    def _check_mouse_pos(self):
        x, y = self.winfo_pointerxy()
        # If mouse is not within the player's area, hide it
        if not (self.winfo_x() <= x <= self.winfo_x() + self.winfo_width()):
            self.withdraw()

    # --- Action Logic ---
    def run_async(self, action):
        async def cmd():
            s = await SessionManager.request_async()
            curr = s.get_current_session()
            if curr:
                if action == "play_pause": await curr.try_toggle_play_pause_async()
                elif action == "next": await curr.try_skip_next_async()
                elif action == "prev": await curr.try_skip_previous_async()
        threading.Thread(target=lambda: asyncio.run(cmd())).start()

    def add_to_startup(self):
        if getattr(sys, 'frozen', False):
            file_path = sys.executable
        else:
            file_path = os.path.realpath(__file__)

        startup_path = os.path.join(winshell.startup(), "MediaControl.lnk")
        try:
            with winshell.shortcut(startup_path) as shortcut:
                shortcut.path = file_path
                shortcut.description = "Media Control Startup"
            ctypes.windll.user32.MessageBoxW(0, "Added to Startup successfully!", "Media Control", 0x40)
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, f"Error: {e}", "Media Control", 0x10)

if __name__ == "__main__":
    app = MediaControlApp()
    app.mainloop()
