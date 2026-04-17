import customtkinter as ctk
import asyncio
import threading
import io
from PIL import Image
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SessionManager
from winrt.windows.storage.streams import Buffer, DataLoader

class MediaFlyout(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.withdraw()

        # Layout
        self.frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#121212", border_width=1, border_color="#333")
        self.frame.pack(padx=5, pady=5, fill="both", expand=True)

        # Album Art
        self.art_label = ctk.CTkLabel(self.frame, text="", width=80, height=80)
        self.art_label.grid(row=0, column=2, rowspan=2, padx=10, pady=10)

        # Info
        self.title_label = ctk.CTkLabel(self.frame, text="Title", font=("Segoe UI", 16, "bold"), anchor="w")
        self.title_label.grid(row=0, column=0, columnspan=2, padx=(15, 0), sticky="w", pady=(10,0))
        
        self.artist_label = ctk.CTkLabel(self.frame, text="Artist", font=("Segoe UI", 12), text_color="#aaa", anchor="w")
        self.artist_label.grid(row=1, column=0, columnspan=2, padx=(15, 0), sticky="nw")

        # Buttons
        btn_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_f.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        ctk.CTkButton(btn_f, text="⏮", width=40, fg_color="transparent", command=lambda: self.run_async("prev")).pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="⏯", width=40, fg_color="transparent", command=lambda: self.run_async("play_pause")).pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="⏭", width=40, fg_color="transparent", command=lambda: self.run_async("next")).pack(side="left", padx=10)

        # Trigger Strip
        self.trigger = ctk.CTkToplevel()
        self.trigger.overrideredirect(True)
        self.trigger.attributes("-topmost", True)
        self.trigger.geometry(f"5x100+{self.winfo_screenwidth()-5}+{self.winfo_screenheight()//2-50}")
        self.trigger.configure(fg_color="#555")
        self.trigger.bind("<Enter>", self.show_player)
        self.bind("<Leave>", self.hide_player)

        threading.Thread(target=self.update_loop, daemon=True).start()

    async def get_art(self, session):
        try:
            ref = await session.try_get_media_properties_async()
            if not ref.thumbnail: return None
            
            stream = await ref.thumbnail.open_read_async()
            reader = DataLoader(stream)
            await reader.load_async(stream.size)
            buffer = reader.read_buffer(stream.size)
            
            # Convert Windows Buffer to Python Bytes
            import ctypes
            addr = ctypes.addressof(ctypes.c_char.from_buffer(buffer))
            data = ctypes.string_at(addr, buffer.length)
            
            img = Image.open(io.BytesIO(data))
            return ctk.CTkImage(img, size=(80, 80))
        except: return None

    async def _update_info(self):
        try:
            sessions = await SessionManager.request_async()
            session = sessions.get_current_session()
            if session:
                props = await session.try_get_media_properties_async()
                self.title_label.configure(text=props.title[:20])
                self.artist_label.configure(text=props.artist[:25])
                
                art = await self.get_art(session)
                if art: self.art_label.configure(image=art)
        except: pass

    def update_loop(self):
        while True:
            asyncio.run(self._update_info())
            import time
            time.sleep(1)

    def show_player(self, e):
        self.geometry(f"320x160+{self.winfo_screenwidth()-330}+{self.winfo_screenheight()//2-80}")
        self.deiconify()

    def hide_player(self, e):
        # Checks if mouse is actually outside the whole app area
        x, y = self.winfo_pointerxy()
        if x < self.winfo_screenwidth()-330: self.withdraw()

    def run_async(self, action):
        async def cmd():
            s = await SessionManager.request_async()
            curr = s.get_current_session()
            if curr:
                if action == "play_pause": await curr.try_toggle_play_pause_async()
                elif action == "next": await curr.try_skip_next_async()
                elif action == "prev": await curr.try_skip_previous_async()
        threading.Thread(target=lambda: asyncio.run(cmd())).start()

if __name__ == "__main__":
    app = MediaFlyout()
    app.mainloop()
