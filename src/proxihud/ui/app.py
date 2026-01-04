import customtkinter as ctk
import tkinter as tk
import threading
import sys
import os
import logging
import platform  # Added for OS detection

from .. import config, capture, ai, updater, utils
from .window import DraggableWindow
from .settings import SettingsDialog
from .startup import StartupWizard

class GameHelperApp(DraggableWindow):
    def __init__(self):
        super().__init__()
        self.title(config.APP_NAME)
        self._setup_window_properties()

        # Data State
        self.history = []
        self.settings = config.load_settings()
        self.update_available = False
        self.update_url = None

        # UI Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # Start App Flow
        self.wizard = StartupWizard(self.main_container, self.launch_hud)
        self.wizard.start()

    def _setup_window_properties(self):
        try: self.iconbitmap(config.resource_path("icon.ico"))
        except: pass

        # Load geometry or default
        geo = config.load_settings().get("geometry", "500x300+50+50")
        try: self.geometry(geo)
        except: self.geometry("500x300+50+50")

        self.configure(fg_color="#1a1a1a")
        self.attributes("-topmost", True)
        self.attributes("-alpha", config.load_settings().get("opacity", 0.9))
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.bind('<ButtonRelease-1>', self.save_geometry)

    def launch_hud(self):
        """Called when Startup Wizard finishes."""
        for widget in self.main_container.winfo_children(): widget.destroy()

        self.overrideredirect(True)
        self._build_hud_ui()

        if config.is_dev(): self.add_debug_controls()
        if capture.is_windows(): self.start_hotkeys()

        threading.Thread(target=self._bg_update_check, daemon=True).start()

    def _build_hud_ui(self):
        # 1. Input Bar (Bottom)
        self.prompt_frame = ctk.CTkFrame(self.main_container, height=36, fg_color="#202020", corner_radius=8)
        self.prompt_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        # Bind dragging to the bottom bar frame
        self.prompt_frame.bind('<Button-1>', self.clickwin)
        self.prompt_frame.bind('<B1-Motion>', self.dragwin)

        # Settings Icon
        ctk.CTkButton(self.prompt_frame, text="⚙️", width=30, fg_color="transparent", hover_color="#333",
                      font=("Segoe UI", 14), command=self.open_settings).pack(side="left", padx=(5, 0), pady=2)

        # Chat Entry
        self.prompt_entry = ctk.CTkEntry(self.prompt_frame, placeholder_text="Ask...", font=("Segoe UI", 12),
                                         border_width=0, fg_color="transparent", text_color="#eee", height=30)
        self.prompt_entry.pack(side="left", fill="both", expand=True, padx=(5, 60), pady=2)
        self.prompt_entry.bind("<Return>", self.trigger_chat)

        # --- FIX 1: FORCE FOCUS ON CLICK ---
        def on_entry_click(event):
            self.prompt_entry.focus_force()
            self.prompt_entry.focus_set()
        self.prompt_entry.bind("<Button-1>", on_entry_click)
        # -----------------------------------

        # 2. Resize Grip
        self.resize_grip = ctk.CTkLabel(self.prompt_frame, text="↘", font=("Arial", 16), text_color="#555", cursor="sizing", width=30)
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)
        self.resize_grip.bind("<ButtonRelease-1>", self.save_geometry)

        # 3. Text Area
        # --- FIX 2: CURSOR="ARROW" ---
        self.text_area = tk.Text(self.main_container, bg="#1a1a1a", fg="#e0e0e0", font=("Consolas", 11),
                                 wrap="word", bd=0, highlightthickness=0, padx=15, pady=15,
                                 cursor="arrow") # <--- Stops the "I-Beam" typing cursor
        self.text_area.pack(side="top", fill="both", expand=True)
        self._configure_text_tags()

        # Bind dragging to the text area
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        ver = "Dev Mode" if config.is_dev() else updater.CURRENT_VERSION
        self.append_to_chat("System", f"ProxiHUD Ready ({ver})\n[F11] New Scan | [Type] Chat")

    def _configure_text_tags(self):
        self.text_area.tag_config("user_tag", foreground="#4cc9f0", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_config("ai_tag", foreground="#f72585", font=("Segoe UI", 11, "bold"))
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#ffffff")
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#ffd60a")
        self.text_area.tag_config("bullet", foreground="#ffd60a")

    # --- Logic ---
    def trigger_scan(self):
        self.history = []
        self.append_to_chat("System", "Scanning...", clear=True)
        threading.Thread(target=self._run_ai_pipeline, args=(None,), daemon=True).start()

    def trigger_chat(self, event):
        text = self.prompt_entry.get().strip()
        if not text: return
        self.prompt_entry.delete(0, 'end')
        self.focus()
        self.append_to_chat("You", text)
        self.history.append({"role": "user", "text": text})
        threading.Thread(target=self._run_ai_pipeline, args=(text,), daemon=True).start()

    def _run_ai_pipeline(self, user_text=None):
        try:
            img = capture.capture_screen()
            img.thumbnail((1024, 1024))
            response = ai.analyze_image(img, user_text, self.history, self.settings)
            self.history.append({"role": "model", "text": response})
            self.append_to_chat("Proxi", response)
        except Exception as e:
            logging.error(e, exc_info=True)
            self.append_to_chat("Error", str(e))

    # --- Utilities ---
    def append_to_chat(self, sender, text, clear=False):
        self.text_area.config(state="normal")
        if clear: self.text_area.delete("1.0", "end")
        if sender: self.text_area.insert("end", f"\n{sender}: ", "user_tag" if sender == "You" else "ai_tag")

        clean_text = text.replace("```markdown", "").replace("```", "").strip()
        for line in clean_text.split("\n"):
            line = line.strip()
            if not line: continue
            if line.startswith("#"):
                self.text_area.insert("end", line.lstrip("#").strip() + "\n", "header")
            elif line.startswith(("* ", "- ")):
                self.text_area.insert("end", " • ", "bullet")
                self._insert_bold(line[2:] + "\n")
            else:
                self._insert_bold(line + "\n")

        self.text_area.see("end")
        self.text_area.config(state="disabled")

    def _insert_bold(self, text):
        parts = text.split("**")
        for i, part in enumerate(parts):
            self.text_area.insert("end", part, "bold" if i % 2 else "normal")

    def open_settings(self):
        SettingsDialog(self, self.settings, self._apply_settings)

    def _apply_settings(self, new_settings):
        self.settings = new_settings
        self.attributes("-alpha", self.settings["opacity"])
        config.save_settings(self.settings)

    # --- Resizing Logic ---
    def start_resize(self, e):
        self._rx, self._ry, self._rw = e.x_root, e.y_root, self.winfo_width()
        return "break"
    def perform_resize(self, e):
        new_w = max(350, self._rw + (e.x_root - self._rx))
        self.geometry(f"{new_w}x{self.winfo_height()}")
        return "break"
    def save_geometry(self, event=None):
        current = self.geometry()
        if current != self.settings.get("geometry"):
            self.settings["geometry"] = current
            config.save_settings(self.settings)

    # --- System ---
    def start_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(self.settings.get("hotkey_trigger", "f11"), self.trigger_scan)
            keyboard.add_hotkey(self.settings.get("hotkey_exit", "f12"), self.quit_app)
        except ImportError: pass

    def quit_app(self):
        self.save_geometry()
        self.quit()
        sys.exit()

    def _bg_update_check(self):
        import time; time.sleep(2)
        avail, url, ver, msg = updater.check_for_updates()
        if avail:
            self.update_available = True
            self.update_url = url
            self.text_area.bind("<Button-3>", lambda e: updater.update_app(url))
            self.append_to_chat("System", f"Update {ver} available! Right-click here to install.")

    # --- Dev Tools (FIXED INDENTATION & COMMANDS) ---
    def add_debug_controls(self):
        debug_frame = ctk.CTkFrame(self.main_container, height=30, fg_color="#333333")
        debug_frame.pack(side="bottom", fill="x")
        # Ensure 'command=self.debug_save' refers to the method below
        ctk.CTkButton(debug_frame, text="Dump", width=60, height=20, fg_color="#444", command=self.debug_save).pack(side="left", padx=5)
        ctk.CTkButton(debug_frame, text="Mock", width=60, height=20, fg_color="#444", command=self.debug_load).pack(side="left", padx=5)

    def debug_save(self):
        try:
            capture.capture_screen().save("debug.png")
            # Cross-platform open command
            if platform.system() == "Darwin": # macOS
                os.system("open debug.png")
            else: # Windows
                os.system("start debug.png")
        except Exception as e:
            logging.error(f"Debug dump failed: {e}")

    def debug_load(self):
        threading.Thread(target=lambda: self._run_ai_pipeline(self.prompt_entry.get() or None), daemon=True).start()