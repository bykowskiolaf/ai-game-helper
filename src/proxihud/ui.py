import customtkinter as ctk
import tkinter as tk
import threading
import sys
import os
import logging
from PIL import Image
from . import config, capture, ai, updater, utils

# --- API KEY ROW WIDGET ---
class ApiKeyRow(ctk.CTkFrame):
    def __init__(self, parent, key_text, remove_callback):
        super().__init__(parent, fg_color="transparent")
        self.pack(fill="x", pady=2)
        
        # Entry (Masked by default)
        self.entry = ctk.CTkEntry(self, show="∗", height=28)
        self.entry.insert(0, key_text)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Toggle Visibility Button
        self.visible = False
        self.eye_btn = ctk.CTkButton(
            self, text="👁", width=25, height=28, 
            fg_color="#333", hover_color="#444", 
            command=self.toggle_visibility
        )
        self.eye_btn.pack(side="left", padx=(0, 2))

        # Delete Button
        self.del_btn = ctk.CTkButton(
            self, text="❌", width=25, height=28, 
            fg_color="#8B0000", hover_color="#B22222",
            command=lambda: remove_callback(self)
        )
        self.del_btn.pack(side="left")

    def toggle_visibility(self):
        self.visible = not self.visible
        self.entry.configure(show="" if self.visible else "∗")
        self.eye_btn.configure(fg_color="#555" if self.visible else "#333")

    def get_key(self):
        return self.entry.get().strip()

# --- SETTINGS WINDOW ---
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_settings, apply_callback):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("340x550")
        self.attributes("-topmost", True)
        self.apply_callback = apply_callback
        self.settings = current_settings.copy()
        self.key_rows = []

        # Main Scrollable Container for the whole window
        # (Allows the settings menu to fit on small screens)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # 1. Appearance
        self.add_header("🎨 Appearance")
        ctk.CTkLabel(self.scroll, text="Opacity").pack(anchor="w", padx=10)
        self.opacity_slider = ctk.CTkSlider(self.scroll, from_=0.2, to=1.0, command=self.update_opacity)
        self.opacity_slider.set(self.settings["opacity"])
        self.opacity_slider.pack(fill="x", padx=10, pady=5)

        # 2. Persona
        self.add_header("🧠 AI Persona")
        self.persona_var = ctk.StringVar(value=self.settings["persona"])
        self.persona_combo = ctk.CTkComboBox(
            self.scroll, 
            values=["Default", "Sarcastic", "Brief", "Pirate", "Helpful"],
            variable=self.persona_var,
            command=self.update_persona
        )
        self.persona_combo.pack(fill="x", padx=10, pady=5)

        # 3. API Keys (Dynamic List)
        self.add_header("🔑 API Keys")
        
        self.keys_container = ctk.CTkFrame(self.scroll, fg_color="#2b2b2b", corner_radius=6)
        self.keys_container.pack(fill="x", padx=10, pady=5)
        
        # Load existing keys
        current_keys = config.get_api_keys()
        if not current_keys:
            self.add_key_row("") # Add one empty row if none exist
        else:
            for k in current_keys:
                self.add_key_row(k)

        # Add Key Button
        ctk.CTkButton(
            self.scroll, text="➕ Add Another Key", 
            fg_color="#333", hover_color="#444", 
            command=lambda: self.add_key_row("")
        ).pack(fill="x", padx=10, pady=5)

        # 4. Hotkeys
        self.add_header("⌨️ Hotkeys (Restart to apply)")
        self.trigger_entry = ctk.CTkEntry(self.scroll, placeholder_text="Trigger (e.g. f11)")
        self.trigger_entry.insert(0, self.settings.get("hotkey_trigger", "f11"))
        self.trigger_entry.pack(fill="x", padx=10, pady=2)
        
        # Save Button (Pinned to bottom of window, outside scroll)
        self.save_btn = ctk.CTkButton(self, text="Save & Close", height=40, command=self.save_and_close)
        self.save_btn.pack(side="bottom", fill="x", padx=20, pady=15)

    def add_header(self, text):
        ctk.CTkLabel(self.scroll, text=text, font=("Segoe UI", 13, "bold"), text_color="#ccc").pack(anchor="w", padx=10, pady=(15, 2))

    def add_key_row(self, text):
        row = ApiKeyRow(self.keys_container, text, self.remove_key_row)
        self.key_rows.append(row)

    def remove_key_row(self, row_widget):
        self.key_rows.remove(row_widget)
        row_widget.destroy()

    def update_opacity(self, value):
        self.settings["opacity"] = value
        self.apply_callback(self.settings)

    def update_persona(self, value):
        self.settings["persona"] = value
        self.apply_callback(self.settings)

    def save_and_close(self):
        self.settings["hotkey_trigger"] = self.trigger_entry.get()
        
        # Harvest Keys
        valid_keys = []
        for row in self.key_rows:
            k = row.get_key()
            if k and len(k) > 5: # Basic validation
                valid_keys.append(k)
        
        # Join with commas and save
        key_string = ",".join(valid_keys)
        config.save_api_key(key_string)
        
        self.apply_callback(self.settings)
        self.destroy()

# --- MAIN APP ---
class DraggableWindow(ctk.CTk):
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
        self.focus_force()

    def dragwin(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f'+{x}+{y}')

class GameHelperApp(DraggableWindow):
    def __init__(self):
        super().__init__()
        self.title(config.APP_NAME)
        try: self.iconbitmap(config.resource_path("icon.ico"))
        except: pass

        self.settings = config.load_settings()

        try: self.geometry(self.settings.get("geometry", "500x300+50+50")) 
        except: self.geometry("500x300+50+50")

        self.configure(fg_color="#1a1a1a")
        self.attributes("-topmost", True)
        self.attributes("-alpha", self.settings["opacity"]) 
        self.lift() 
        self.enforce_topmost()

        self.history = [] 

        # Initial Login Check
        if not config.get_api_keys():
            self.show_login()
        else:
            self.show_hud()

        self.bind('<ButtonRelease-1>', self.save_geometry)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.update_available = False
        self.update_url = None
        threading.Thread(target=self.bg_update_check, daemon=True).start()

    def enforce_topmost(self):
        self.lift()
        self.attributes("-topmost", True)
        self.after(2000, self.enforce_topmost)

    def save_geometry(self, event=None):
        current_geo = self.geometry()
        if current_geo != self.settings.get("geometry"):
            self.settings["geometry"] = current_geo
            config.save_settings(self.settings)

    def quit_app(self):
        logging.info("Exiting app...")
        self.save_geometry() 
        self.quit()
        sys.exit()

    def apply_settings(self, new_settings):
        self.settings = new_settings
        self.attributes("-alpha", self.settings["opacity"])
        config.save_settings(self.settings)

    def open_settings(self):
        SettingsDialog(self, self.settings, self.apply_settings)

    def show_login(self):
        self.overrideredirect(False) 
        ctk.CTkLabel(self, text="🔑 ProxiHUD Setup", font=("Segoe UI", 16, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Please enter your Google Gemini API Key below.", font=("Segoe UI", 12), text_color="gray").pack(pady=(0, 15))
        
        self.entry = ctk.CTkEntry(self, width=300, placeholder_text="Paste API Key here...")
        self.entry.pack()
        self.entry.bind("<Return>", self.save_key)
        
        ctk.CTkButton(self, text="Save & Start", command=lambda: self.save_key(None)).pack(pady=10)

    def save_key(self, event):
        key = self.entry.get().strip()
        if len(key) > 5:
            config.save_api_key(key)
            for widget in self.winfo_children(): widget.destroy()
            self.show_hud()

    def show_hud(self):
        self.overrideredirect(True) 
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True)

        if config.is_dev(): self.add_debug_controls()

        # Input Bar
        self.prompt_frame = ctk.CTkFrame(self.frame, height=36, fg_color="#202020", corner_radius=8)
        self.prompt_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.prompt_frame.bind('<Button-1>', self.clickwin)
        self.prompt_frame.bind('<B1-Motion>', self.dragwin)

        # Settings Button
        self.settings_btn = ctk.CTkButton(
            self.prompt_frame, text="⚙️", width=30, fg_color="transparent", hover_color="#333",
            font=("Segoe UI", 14), command=self.open_settings
        )
        self.settings_btn.pack(side="left", padx=(5, 0), pady=2)

        # Entry
        self.prompt_entry = ctk.CTkEntry(
            self.prompt_frame, placeholder_text="Ask...", font=("Segoe UI", 12), 
            border_width=0, fg_color="transparent", text_color="#eee", height=30
        )
        self.prompt_entry.pack(side="left", fill="both", expand=True, padx=(5, 60), pady=2)
        self.prompt_entry.bind("<Return>", self.trigger_chat)
        
        def on_entry_click(event):
            self.prompt_entry.focus_force()
            self.prompt_entry.focus_set()
            return "break"
        self.prompt_entry.bind("<Button-1>", on_entry_click)

        # Separator & Grip
        ctk.CTkFrame(self.prompt_frame, width=2, height=18, fg_color="#333", corner_radius=1).place(relx=1.0, rely=0.5, anchor="e", x=-35, y=0)
        
        self.resize_grip = ctk.CTkLabel(self.prompt_frame, text="↘", font=("Arial", 16), text_color="#555", cursor="sizing", width=30, height=30)
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2) 
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)
        self.resize_grip.bind("<ButtonRelease-1>", self.save_geometry)

        # Text Area
        self.text_area = tk.Text(self.frame, bg="#1a1a1a", fg="#e0e0e0", font=("Consolas", 11), wrap="word", bd=0, highlightthickness=0, padx=15, pady=15)
        self.text_area.pack(side="top", fill="both", expand=True)

        self.text_area.tag_config("user_tag", foreground="#4cc9f0", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_config("ai_tag", foreground="#f72585", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#ffffff")
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#ffd60a")
        self.text_area.tag_config("bullet", foreground="#ffd60a")

        if config.is_dev(): ver = "Dev Mode"
        else: ver = updater.CURRENT_VERSION
        
        self.append_to_chat("System", f"ProxiHUD Ready ({ver})\n[F11] New Scan | [Type] Chat")

        self.text_area.bind("<Button-3>", self.trigger_update_or_clear) 
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        if capture.is_windows(): self.start_hotkeys()

    def add_debug_controls(self):
        debug_frame = ctk.CTkFrame(self.frame, height=30, fg_color="#333333")
        debug_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(debug_frame, text="Dump", width=60, height=20, fg_color="#444", command=self.debug_save).pack(side="left", padx=5)
        ctk.CTkButton(debug_frame, text="Mock", width=60, height=20, fg_color="#444", command=self.debug_load).pack(side="left", padx=5)

    # --- CHAT & LOGIC ---
    def append_to_chat(self, sender, text, clear=False):
        self.text_area.config(state="normal")
        if clear: self.text_area.delete("1.0", "end")
        if sender: self.text_area.insert("end", f"\n{sender}: ", "user_tag" if sender == "You" else "ai_tag")
        
        clean_text = text.replace("```markdown", "").replace("```", "").strip()
        for line in clean_text.split("\n"):
            line = line.strip()
            if not line: continue
            if line.startswith("#"): self.text_area.insert("end", line.lstrip("#").strip() + "\n", "header")
            elif line.startswith(("* ", "- ")): 
                self.text_area.insert("end", " • ", "bullet")
                self._insert_bold(line[2:])
                self.text_area.insert("end", "\n")
            else: 
                self._insert_bold(line)
                self.text_area.insert("end", "\n")
        
        self.text_area.see("end")
        self.text_area.config(state="disabled")

    def _insert_bold(self, text):
        for i, part in enumerate(text.split("**")):
            self.text_area.insert("end", part, "bold" if i % 2 else "normal")

    def trigger_scan(self):
        self.history = []
        self.append_to_chat("System", "Scanning...", clear=True)
        threading.Thread(target=self.run_logic, args=(None,), daemon=True).start()

    def trigger_chat(self, event):
        text = self.prompt_entry.get().strip()
        if not text: return
        self.prompt_entry.delete(0, 'end')
        self.focus()
        self.append_to_chat("You", text)
        self.history.append({"role": "user", "text": text})
        threading.Thread(target=self.run_logic, args=(text,), daemon=True).start()

    def run_logic(self, user_text=None):
        try:
            img = capture.capture_screen()
            img.thumbnail((1024, 1024))
            response = ai.analyze_image(img, user_text, self.history, self.settings)
            self.history.append({"role": "model", "text": response})
            self.append_to_chat("Proxi", response)
        except Exception as e:
            self.append_to_chat("Error", str(e))

    def start_resize(self, e): 
        self._rx, self._ry, self._rw = e.x_root, e.y_root, self.winfo_width()
        return "break"
    def perform_resize(self, e): 
        self.geometry(f"{max(350, self._rw + (e.x_root - self._rx))}x{self.winfo_height()}")
        self.render_markdown(self.text_area.get("1.0", "end-1c"))
        return "break"

    def start_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(self.settings.get("hotkey_trigger", "f11"), self.trigger_scan)
            keyboard.add_hotkey(self.settings.get("hotkey_exit", "f12"), self.quit_app) 
        except: pass

    def debug_save(self): capture.capture_screen().save("debug.png"); os.system("start debug.png")
    def debug_load(self): threading.Thread(target=lambda: self.run_logic(self.prompt_entry.get() or None), daemon=True).start()
    
    def bg_update_check(self):
        import time; time.sleep(1)
        avail, url, ver, msg = updater.check_for_updates()
        if avail: 
            self.update_url = url; self.new_ver = ver
            self.append_to_chat("System", f"Update {ver} available. Right-click to install.")
            self.update_available = True

    def trigger_update_or_clear(self, e):
        if self.update_available:
            self.append_to_chat("System", "Updating...")
            threading.Thread(target=updater.update_app, args=(self.update_url,), daemon=True).start()
    
    def render_markdown(self, raw): self.append_to_chat(None, raw, clear=True)