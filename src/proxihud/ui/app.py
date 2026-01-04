import customtkinter as ctk
import tkinter as tk
import threading
import sys
import os
import logging
from PIL import Image

from .. import config, capture, ai, updater, utils
from .window import DraggableWindow
from .settings import SettingsDialog

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
        
        # --- VIEW MANAGER ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

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

    def clear_view(self):
        """Removes all widgets from the main container"""
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # --- LOGIN VIEW ---
    # --- LOGIN VIEW ---
    def show_login(self):
        self.overrideredirect(False) 
        self.clear_view()
        
        # Center the Login Content
        content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(content, text="🔑 ProxiHUD Setup", font=("Segoe UI", 16, "bold")).pack(pady=(0, 5))
        ctk.CTkLabel(content, text="Enter your Gemini API Key", font=("Segoe UI", 12), text_color="gray").pack(pady=(0, 15))
        
        self.login_entry = ctk.CTkEntry(content, width=280, placeholder_text="Paste Key here...")
        self.login_entry.pack(pady=5)
        self.login_entry.bind("<Return>", self.save_key_from_login)
        
        def on_login_click(event):
            self.login_entry.focus_force()
            self.login_entry.focus_set()
            return "break"
        
        self.login_entry.bind("<Button-1>", on_login_click)
        # ------------------------------------------

        ctk.CTkButton(content, text="Save & Start", command=lambda: self.save_key_from_login(None)).pack(pady=10)

    def save_key_from_login(self, event):
        key = self.login_entry.get().strip()
        if len(key) > 5:
            config.save_api_key(key)
            self.show_hud()

    # --- HUD VIEW ---
    def show_hud(self):
        self.overrideredirect(True) 
        self.clear_view()

        # Debug Bar (Dev Only)
        if config.is_dev(): self.add_debug_controls()

        # Input Bar (Bottom)
        self.prompt_frame = ctk.CTkFrame(self.main_container, height=36, fg_color="#202020", corner_radius=8)
        self.prompt_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.prompt_frame.bind('<Button-1>', self.clickwin)
        self.prompt_frame.bind('<B1-Motion>', self.dragwin)

        # Settings Button
        self.settings_btn = ctk.CTkButton(
            self.prompt_frame, text="⚙️", width=30, fg_color="transparent", hover_color="#333",
            font=("Segoe UI", 14), command=self.open_settings
        )
        self.settings_btn.pack(side="left", padx=(5, 0), pady=2)

        # Chat Entry
        self.prompt_entry = ctk.CTkEntry(
            self.prompt_frame, placeholder_text="Ask...", font=("Segoe UI", 12), 
            border_width=0, fg_color="transparent", text_color="#eee", height=30
        )
        self.prompt_entry.pack(side="left", fill="both", expand=True, padx=(5, 60), pady=2)
        self.prompt_entry.bind("<Return>", self.trigger_chat)
        
        # Entry Focus Logic
        def on_entry_click(event):
            self.prompt_entry.focus_force()
            self.prompt_entry.focus_set()
            return "break"
        self.prompt_entry.bind("<Button-1>", on_entry_click)

        # Separator
        ctk.CTkFrame(self.prompt_frame, width=2, height=18, fg_color="#333", corner_radius=1).place(relx=1.0, rely=0.5, anchor="e", x=-35, y=0)
        
        # Resize Grip
        self.resize_grip = ctk.CTkLabel(self.prompt_frame, text="↘", font=("Arial", 16), text_color="#555", cursor="sizing", width=30, height=30)
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2) 
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)
        self.resize_grip.bind("<ButtonRelease-1>", self.save_geometry)

        # Text Area (Top)
        self.text_area = tk.Text(self.main_container, bg="#1a1a1a", fg="#e0e0e0", font=("Consolas", 11), wrap="word", bd=0, highlightthickness=0, padx=15, pady=15)
        self.text_area.pack(side="top", fill="both", expand=True)

        # Text Styles
        self.text_area.tag_config("user_tag", foreground="#4cc9f0", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_config("ai_tag", foreground="#f72585", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#ffffff")
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#ffd60a")
        self.text_area.tag_config("bullet", foreground="#ffd60a")

        # Ready Message
        ver = "Dev Mode" if config.is_dev() else updater.CURRENT_VERSION
        self.append_to_chat("System", f"ProxiHUD Ready ({ver})\n[F11] New Scan | [Type] Chat")

        # Bindings
        self.text_area.bind("<Button-3>", self.trigger_update_or_clear) 
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        if capture.is_windows(): self.start_hotkeys()

    def add_debug_controls(self):
        debug_frame = ctk.CTkFrame(self.main_container, height=30, fg_color="#333333")
        debug_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(debug_frame, text="Dump", width=60, height=20, fg_color="#444", command=self.debug_save).pack(side="left", padx=5)
        ctk.CTkButton(debug_frame, text="Mock", width=60, height=20, fg_color="#444", command=self.debug_load).pack(side="left", padx=5)

    # --- LOGIC ---
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
    def save_geometry(self, event=None):
        current_geo = self.geometry()
        if current_geo != self.settings.get("geometry"):
            self.settings["geometry"] = current_geo
            config.save_settings(self.settings)

    def start_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(self.settings.get("hotkey_trigger", "f11"), self.trigger_scan)
            keyboard.add_hotkey(self.settings.get("hotkey_exit", "f12"), self.quit_app) 
        except: pass

    def quit_app(self):
        logging.info("Exiting app...")
        self.save_geometry() 
        self.quit()
        sys.exit()

    def open_settings(self):
        SettingsDialog(self, self.settings, self.apply_settings)
    
    def apply_settings(self, new_settings):
        self.settings = new_settings
        self.attributes("-alpha", self.settings["opacity"])
        config.save_settings(self.settings)

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