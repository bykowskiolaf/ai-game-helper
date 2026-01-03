import customtkinter as ctk
import tkinter as tk
import threading
import config
import capture
import ai
import updater

class DraggableWindow(ctk.CTk):
    """A frameless window that can be dragged"""
    def __init__(self):
        super().__init__()
        self.overrideredirect(True) # Removes Title Bar & Borders
        self._offsetx = 0
        self._offsety = 0
        self.bind('<Button-1>', self.clickwin)
        self.bind('<B1-Motion>', self.dragwin)

    def clickwin(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def dragwin(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f'+{x}+{y}')

class GameHelperApp(DraggableWindow):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.geometry("400x150+50+50") 
        self.configure(fg_color="#1a1a1a") # Dark background
        
        # --- FORCE ON TOP SETTINGS ---
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.80) 
        self.lift() # Lift to top immediately
        
        # Start the "Watchdog" to keep it on top
        self.enforce_topmost()

        # Check API Key
        if not config.get_api_key():
            self.show_login()
        else:
            self.show_hud()

        self.update_available = False
        self.update_url = None
        threading.Thread(target=self.bg_update_check, daemon=True).start()

    def enforce_topmost(self):
        """Forces the window to the top layer every 2 seconds"""
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
            config.save_api_key(key)
            for widget in self.winfo_children(): widget.destroy()
            self.show_hud()

    def show_hud(self):
        self.overrideredirect(True) 
        
        # Text Area (HUD Style)
        self.text_area = tk.Text(
            self, 
            bg="#1a1a1a", 
            fg="#e0e0e0", 
            font=("Consolas", 11), 
            wrap="word", 
            bd=0, 
            highlightthickness=0,
            padx=10, pady=10
        )
        self.text_area.pack(fill="both", expand=True)
        
        # Markdown Styles
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#4cc9f0")
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#f72585")
        self.text_area.tag_config("bullet", foreground="#ffd60a")

        self.render_markdown(f"READY\n[F11] Analyze\n[F12] Quit")

        # Bindings
        self.text_area.bind("<Button-3>", lambda e: self.render_markdown("")) # Right-click to clear
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        if capture.is_windows():
            self.start_hotkeys()

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

        self.text_area.config(state="disabled") 
        
        # Auto-Resize Window Height
        num_lines = int(self.text_area.index('end-1c').split('.')[0])
        new_height = min(600, max(100, num_lines * 20 + 30))
        self.geometry(f"400x{new_height}")

    def run_analysis_thread(self):
        t = threading.Thread(target=self.run_logic, daemon=True)
        t.start()

    def run_logic(self):
        self.render_markdown("... 👀 Looking ...")
        try:
            img = capture.capture_screen()
            img.thumbnail((1024, 1024))
            self.render_markdown("... 🧠 Thinking ...")
            result = ai.analyze_image(img)
            self.render_markdown(result)
        except Exception as e:
            self.render_markdown(f"Error: {e}")

    def start_hotkeys(self):
        try:
            import keyboard
            def listen():
                keyboard.add_hotkey(config.TRIGGER_KEY, self.run_analysis_thread)
                keyboard.add_hotkey(config.EXIT_KEY, self.quit)
                keyboard.wait()
            threading.Thread(target=listen, daemon=True).start()
        except ImportError:
            pass

    def bg_update_check(self):
        """Runs silently on startup"""
        available, url, version = updater.check_for_updates()
        if available:
            self.update_available = True
            self.update_url = url
            self.new_version = version
            # If HUD is already open, show the alert
            if hasattr(self, 'text_area'):
                self.show_update_alert()

    def show_update_alert(self):
        """Injects a link into the Markdown text"""
        msg = f"\n\n🚨 UPDATE AVAILABLE: {self.new_version}\n[Right-Click to Update Now]"
        # We append this to the text area
        self.render_markdown(self.text_area.get("1.0", "end") + msg)
        # Bind Right-Click to Trigger Update (Override the 'Clear' binding if update exists)
        self.text_area.bind("<Button-3>", self.trigger_update)

    def trigger_update(self, event):
        if self.update_available:
            self.render_markdown(f"⬇ Downloading {self.new_version}...\nPlease wait, app will restart.")
            # Run download in thread to avoid freezing UI
            threading.Thread(target=updater.update_app, args=(self.update_url,), daemon=True).start()
        else:
            # Standard Clear behavior
            self.render_markdown("")