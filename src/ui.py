import customtkinter as ctk
import tkinter as tk
import threading
import config
import capture
import ai
import updater

class DraggableWindow(ctk.CTk):
    """A frameless window that can be dragged and resized"""
    def __init__(self):
        super().__init__()
        self.overrideredirect(True) 
        self._offsetx = 0
        self._offsety = 0

        # Bind moving logic to the background
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
        
        # Initial Size (Wider by default)
        self.geometry("500x150+50+50") 
        self.configure(fg_color="#1a1a1a")
        
        # --- FORCE ON TOP SETTINGS ---
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.80) 
        self.lift() 
        self.enforce_topmost()

        # Check API Key
        if not config.get_api_key():
            self.show_login()
        else:
            self.show_hud()

        # Update Check
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
            config.save_api_key(key)
            for widget in self.winfo_children(): widget.destroy()
            self.show_hud()

    def show_hud(self):
        self.overrideredirect(True) 
        
        # Main Layout Frame
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True)

        # Text Area
        self.text_area = tk.Text(
            self.frame, 
            bg="#1a1a1a", 
            fg="#e0e0e0", 
            font=("Consolas", 11), 
            wrap="word", 
            bd=0, 
            highlightthickness=0,
            padx=10, pady=10
        )
        self.text_area.pack(fill="both", expand=True)
        
        # --- RESIZE GRIP (Bottom Right) ---
        self.resize_grip = ctk.CTkLabel(
            self.frame, 
            text="↘", 
            font=("Arial", 12), 
            text_color="gray", 
            cursor="sizing"
        )
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)
        
        # Bind Resize Logic
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)

        # Markdown Styles
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#4cc9f0")
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#f72585")
        self.text_area.tag_config("bullet", foreground="#ffd60a")

        # Initial Text
        ver = updater.CURRENT_VERSION
        self.render_markdown(f"READY ({ver})\n[F11] Analyze\n[F12] Quit\n(Drag ↘ to resize)")

        # Bindings (Pass drag through text area)
        self.text_area.bind("<Button-3>", self.trigger_update_or_clear) 
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        if capture.is_windows():
            self.start_hotkeys()

    # --- RESIZE LOGIC ---
    def start_resize(self, event):
        self._resize_x = event.x_root
        self._resize_y = event.y_root
        self._start_width = self.winfo_width()
        return "break"

    def perform_resize(self, event):
        # Calculate new width based on mouse movement
        delta_x = event.x_root - self._resize_x
        new_width = max(200, self._start_width + delta_x)
        
        # Apply new width
        self.geometry(f"{new_width}x{self.winfo_height()}")
        
        # Force text re-wrap
        self.render_markdown(self.text_area.get("1.0", "end-1c"))
        return "break"

    def render_markdown(self, raw_text):
        """Renders text and Auto-Resizes HEIGHT to fit"""
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
        
        # --- AUTO-FIT HEIGHT ---
        self.text_area.update_idletasks() 
        
        # Count display lines (handling wrapping)
        count = self.text_area.count("1.0", "end", "displaylines")
        num_display_lines = count[0] if count else 1

        import tkinter.font as tkfont
        font = tkfont.Font(family="Consolas", size=11)
        line_height = font.metrics("linespace")

        # Buffer for padding + header spacing
        required_height = (num_display_lines * line_height) + 40
        final_height = max(80, min(800, required_height))
        
        # Preserve CURRENT Width (allow user to resize width, we auto-fit height)
        current_width = self.winfo_width()
        if current_width < 100: current_width = 500 # Default wider
            
        x = self.winfo_x()
        y = self.winfo_y()
        self.geometry(f"{current_width}x{final_height}+{x}+{y}")

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
        # Small delay to ensure HUD is rendered
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
        current_text = self.text_area.get("1.0", "end-1c")
        msg = f"\n\n🚨 UPDATE AVAILABLE: {self.new_version}\n[Right-Click to Update Now]"
        self.render_markdown(current_text + msg)

    def trigger_update_or_clear(self, event):
        if self.update_available:
            self.render_markdown(f"⬇ Downloading {self.new_version}...\nPlease wait, app will restart.")
            threading.Thread(target=updater.update_app, args=(self.update_url,), daemon=True).start()
        else:
            self.render_markdown(f"READY ({updater.CURRENT_VERSION})\n[F11] Analyze\n[F12] Quit")