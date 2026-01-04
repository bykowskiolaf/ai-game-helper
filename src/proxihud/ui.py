import customtkinter as ctk
import tkinter as tk
import threading
import sys
import os
import logging
from PIL import Image
from . import config
from . import capture
from . import ai
from . import updater

class DraggableWindow(ctk.CTk):
    """A frameless window that can be dragged and resized"""
    def __init__(self):
        super().__init__()
        self.overrideredirect(True) 
        self._offsetx = 0
        self._offsety = 0
        self.bind('<Button-1>', self.clickwin)
        self.bind('<B1-Motion>', self.dragwin)

    def clickwin(self, event):
        self._offsetx = event.x
        self._offsety = event.y
        # FIX: Force focus to main window on click too
        self.focus_force()

    def dragwin(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f'+{x}+{y}')

class GameHelperApp(DraggableWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Setup Title & Icon
        self.title(config.APP_NAME)
        try:
            self.iconbitmap(config.resource_path("icon.ico"))
        except: pass

        # 2. Window Setup
        self.geometry("500x250+50+50") 
        self.configure(fg_color="#1a1a1a")
        
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.90) 
        self.lift() 
        self.enforce_topmost()

        if not config.get_api_key():
            self.show_login()
        else:
            self.show_hud()

        # Background Update Check
        self.update_available = False
        self.update_url = None
        threading.Thread(target=self.bg_update_check, daemon=True).start()

    def enforce_topmost(self):
        self.lift()
        self.attributes("-topmost", True)
        self.after(2000, self.enforce_topmost)

    def show_login(self):
        self.overrideredirect(False) 
        ctk.CTkLabel(self, text="🔑 Enter API Key & Press Enter", font=("Segoe UI", 14, "bold")).pack(pady=20)
        self.entry = ctk.CTkEntry(self, width=300)
        self.entry.pack()
        self.entry.bind("<Return>", self.save_key)

    def save_key(self, event):
        key = self.entry.get().strip()
        if len(key) > 5:
            logging.info("User saved a new API Key")
            config.save_api_key(key)
            for widget in self.winfo_children(): widget.destroy()
            self.show_hud()

    def show_hud(self):
        self.overrideredirect(True) 
        
        # Main Container
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True)

        # --- LAYOUT STACKING (Bottom Up) ---
        
        # 1. Debug Controls (Bottom Priority)
        if not getattr(sys, 'frozen', False):
            self.add_debug_controls()

        # 2. PROMPT ENTRY (New Feature - Stacks above Debug)
        self.prompt_frame = ctk.CTkFrame(self.frame, height=30, fg_color="#2b2b2b")
        self.prompt_frame.pack(side="bottom", fill="x", padx=2, pady=2)
        
        self.prompt_entry = ctk.CTkEntry(
            self.prompt_frame, 
            placeholder_text="Type question... (e.g. 'How much is this worth?')",
            font=("Consolas", 11),
            border_width=0,
            fg_color="#333",
            text_color="#eee"
        )
        self.prompt_entry.pack(side="left", fill="both", expand=True, padx=(2, 0))
        self.prompt_entry.bind("<Return>", self.trigger_custom_analysis)

        # --- [FIX] FORCE FOCUS ON CLICK ---
        # Frameless windows don't get focus automatically. We force it.
        def on_entry_click(event):
            self.prompt_entry.focus_force()
            self.prompt_entry.focus_set()
            return "break" # Stop the click from triggering window drag
            
        self.prompt_entry.bind("<Button-1>", on_entry_click)


        # Send Button
        self.send_btn = ctk.CTkButton(
            self.prompt_frame, text="➤", width=30, fg_color="#444", hover_color="#555",
            command=lambda: self.trigger_custom_analysis(None)
        )
        self.send_btn.pack(side="right", padx=2)

        # 3. TEXT AREA (Takes remaining space at Top)
        self.text_area = tk.Text(
            self.frame, 
            bg="#1a1a1a", fg="#e0e0e0", 
            font=("Consolas", 11), wrap="word", 
            bd=0, highlightthickness=0, padx=10, pady=10
        )
        self.text_area.pack(side="top", fill="both", expand=True)
        
        # Resize Grip (Overlay on bottom right)
        self.resize_grip = ctk.CTkLabel(self.frame, text="↘", font=("Arial", 12), text_color="gray", cursor="sizing")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=0) 
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)

        # Config Styles
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#4cc9f0")
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#f72585")
        self.text_area.tag_config("bullet", foreground="#ffd60a")

        # Initial Text
        ver = updater.CURRENT_VERSION
        self.render_markdown(f"READY ({ver})\n[F11] Auto-Analyze\n[Type] Custom Question")
        
        self.text_area.bind("<Button-3>", self.trigger_update_or_clear) 
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        if capture.is_windows():
            self.start_hotkeys()

    def add_debug_controls(self):
        debug_frame = ctk.CTkFrame(self.frame, height=30, fg_color="#333333")
        debug_frame.pack(side="bottom", fill="x")

        ctk.CTkButton(
            debug_frame, text="💾 Save Dump", width=80, height=20, 
            font=("Arial", 10), fg_color="#444", command=self.debug_save_screenshot
        ).pack(side="left", padx=5, pady=2)

        ctk.CTkButton(
            debug_frame, text="📂 Load Mock", width=80, height=20, 
            font=("Arial", 10), fg_color="#444", command=self.debug_load_mock
        ).pack(side="left", padx=5, pady=2)

    def trigger_custom_analysis(self, event):
        user_text = self.prompt_entry.get().strip()
        if not user_text:
            return 
            
        self.prompt_entry.delete(0, 'end') 
        self.render_markdown(f"💬 Asking: '{user_text}'...")
        # Unfocus the entry so hotkeys work immediately again
        self.focus() 
        
        # Run custom query in thread
        threading.Thread(target=self.run_logic, args=(user_text,), daemon=True).start()

    def run_analysis_thread(self):
        """Called by F11 (Auto Mode)"""
        logging.info("Analysis triggered (Auto)")
        self.render_markdown("... 👀 Looking ...")
        t = threading.Thread(target=self.run_logic, args=(None,), daemon=True) 
        t.start()

    def run_logic(self, user_text=None):
        try:
            img = capture.capture_screen()
            img.thumbnail((1024, 1024))
            
            if user_text:
                logging.info(f"Running custom query: {user_text}")
            
            self.finish_analysis(img, user_text)
        except Exception as e:
            logging.error(f"Capture error: {e}")
            self.render_markdown(f"Error: {e}")

    def finish_analysis(self, img, user_text=None):
        try:
            result = ai.analyze_image(img, user_prompt=user_text)
            self.render_markdown(result)
        except Exception as e:
            self.render_markdown(f"AI Error: {e}")

    # --- DEBUG TOOLS ---
    def debug_save_screenshot(self):
        try:
            logging.info("Debug: Saving screenshot dump")
            img = capture.capture_screen()
            img.save("debug.png")
            self.render_markdown(f"✅ Saved 'debug.png'.")
            if os.name == 'nt': os.startfile("debug.png")
            else: os.system("open debug.png")
        except Exception as e:
            logging.error(f"Debug screenshot failed: {e}")

    def debug_load_mock(self):
        try:
            if not os.path.exists("mock.png"):
                self.render_markdown("❌ ERROR: 'mock.png' not found.")
                return
            
            logging.info("Debug: Loading mock image")
            img = Image.open("mock.png")
            user_text = self.prompt_entry.get().strip()
            if not user_text: user_text = None
            
            threading.Thread(target=lambda: self.finish_analysis(img, user_text), daemon=True).start()
        except Exception as e:
            logging.error(f"Debug load mock failed: {e}")

    # --- RESIZE LOGIC ---
    def start_resize(self, event):
        self._resize_x = event.x_root
        self._resize_y = event.y_root
        self._start_width = self.winfo_width()
        return "break"

    def perform_resize(self, event):
        delta_x = event.x_root - self._resize_x
        new_width = max(350, self._start_width + delta_x)
        self.geometry(f"{new_width}x{self.winfo_height()}")
        self.render_markdown(self.text_area.get("1.0", "end-1c"))
        return "break"

    def render_markdown(self, raw_text):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", "end")
        
        lines = raw_text.split("\n")
        for line in lines:
            if line.startswith("#"):
                self.text_area.insert("end", line.replace("#", "").strip() + "\n", "header")
            elif line.strip().startswith("* ") or line.strip().startswith("- "):
                self.text_area.insert("end", " • " + line.strip()[2:] + "\n", "bullet")
            else:
                parts = line.split("**")
                for i, part in enumerate(parts):
                    tag = "bold" if i % 2 == 1 else "normal"
                    self.text_area.insert("end", part, tag)
                self.text_area.insert("end", "\n")

        self.text_area.delete("end-1c", "end")
        self.text_area.config(state="disabled") 
        
        self.text_area.update_idletasks() 
        count = self.text_area.count("1.0", "end", "displaylines")
        num_lines = count[0] if count else 1

        import tkinter.font as tkfont
        font = tkfont.Font(family="Consolas", size=11)
        line_height = font.metrics("linespace")

        extra_padding = 40 
        if not getattr(sys, 'frozen', False): extra_padding += 30 
        extra_padding += 40 

        required_height = (num_lines * line_height) + extra_padding
        final_height = max(150, min(800, required_height))
        
        current_width = self.winfo_width()
        if current_width < 100: current_width = 500
            
        x = self.winfo_x()
        y = self.winfo_y()
        self.geometry(f"{current_width}x{final_height}+{x}+{y}")

    def start_hotkeys(self):
        try:
            import keyboard
            def listen():
                keyboard.add_hotkey(config.TRIGGER_KEY, self.run_analysis_thread)
                keyboard.add_hotkey(config.EXIT_KEY, self.quit)
                keyboard.wait()
            threading.Thread(target=listen, daemon=True).start()
        except ImportError: pass

    def bg_update_check(self):
        import time
        time.sleep(1)
        available, url, version, msg = updater.check_for_updates()
        if available:
            self.update_available = True
            self.update_url = url
            self.new_version = version
            if hasattr(self, 'text_area'):
                self.show_update_alert()

    def show_update_alert(self):
        current = self.text_area.get("1.0", "end-1c")
        msg = f"\n\n🚨 UPDATE: {self.new_version}\n[Right-Click to Update]"
        self.render_markdown(current + msg)

    def trigger_update_or_clear(self, event):
        if self.update_available:
            logging.info("User triggered update download")
            self.render_markdown(f"⬇ Downloading {self.new_version}...")
            threading.Thread(target=updater.update_app, args=(self.update_url,), daemon=True).start()
        else:
            self.render_markdown(f"READY ({updater.CURRENT_VERSION})")