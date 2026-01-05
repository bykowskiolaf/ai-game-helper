import customtkinter as ctk
import tkinter as tk
import threading
import sys
import os
import logging
import platform

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

        # Force Focus on Click
        def on_entry_click(event):
            self.prompt_entry.focus_force()
            self.prompt_entry.focus_set()
        self.prompt_entry.bind("<Button-1>", on_entry_click)

        # 2. Resize Grip
        self.resize_grip = ctk.CTkLabel(self.prompt_frame, text="↘", font=("Arial", 16), text_color="#555", cursor="sizing", width=30)
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)
        self.resize_grip.bind("<ButtonRelease-1>", self.save_geometry)

        # 3. Text Area
        self.text_area = tk.Text(self.main_container, bg="#1a1a1a", fg="#e0e0e0", font=("Consolas", 11),
                                 wrap="word", bd=0, highlightthickness=0,
                                 padx=15, pady=5,
                                 cursor="arrow")
        self.text_area.pack(side="top", fill="both", expand=True)
        self._configure_text_tags()

        # Bind dragging to the text area
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        ver = "Dev Mode" if config.is_dev() else updater.CURRENT_VERSION
        self.append_to_chat("System", f"ProxiHUD Ready ({ver})\n[F11] New Scan | [Type] Chat")

    def _configure_text_tags(self):
        # Message Headers
        # Reduced spacing1 from 12 to 8 to fix the "gap" look
        self.text_area.tag_config("user_tag", foreground="#4cc9f0", font=("Segoe UI", 11, "bold"), spacing1=8, spacing3=2)
        self.text_area.tag_config("ai_tag", foreground="#f72585", font=("Segoe UI", 11, "bold"), spacing1=8, spacing3=2)

        # Standard Body Text
        self.text_area.tag_config("normal", font=("Consolas", 11), foreground="#e0e0e0", spacing2=3)
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#ffffff", spacing2=3)

        # Headers (Markdown #)
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#ffd60a", spacing1=8, spacing3=4)

        # Bullets
        self.text_area.tag_config("bullet", foreground="#ffd60a", font=("Consolas", 11, "bold"), lmargin1=15, lmargin2=25, spacing2=3)

    def set_status(self, message, color):
        """Updates the status indicator (visual feedback via prompt frame color)."""
        # Map logical colors to hex codes
        color_map = {
            "orange": "#B45309", # Thinking/Working
            "red": "#7F1D1D",    # Error
            "green": "#202020"   # Ready (Default Dark Grey)
        }
        target_color = color_map.get(color, "#202020")

        # Apply color to the bottom prompt frame
        try:
            self.prompt_frame.configure(fg_color=target_color)
            self.update_idletasks() # Force redraw
        except Exception as e:
            logging.error(f"Status update failed: {e}")

    def trigger_scan(self):
        logging.debug("Trigger: Hotkey F11 pressed.")
        self.history = []
        self.append_to_chat("System", "Scanning...", clear=True)
        # Use threading to prevent UI freeze
        threading.Thread(target=self._run_ai_pipeline, args=(None,), daemon=True).start()

    def trigger_chat(self, event):
        text = self.prompt_entry.get().strip()
        if not text: return
        logging.debug(f"Trigger: Chat entered -> {text[:20]}...")
        self.prompt_entry.delete(0, 'end')
        self.focus()
        self.append_to_chat("You", text)
        self.history.append({"role": "user", "text": text})
        threading.Thread(target=self._run_ai_pipeline, args=(text,), daemon=True).start()

    def _run_ai_pipeline(self, prompt_text=None):
        """Main AI Workflow: UI -> Capture -> API -> UI"""
        logging.debug("Pipeline: Starting AI analysis...")

        # 1. Update UI to "Thinking" state
        self.set_status("Analyzing...", "orange")
        self._toggle_loading_state(True)

        # 2. Run Heavy Task in Background Thread
        def task():
            try:
                # A. Capture
                img = capture.capture_screen()
                logging.debug(f"Pipeline: Screen captured. Size={img.size}")

                # B. Determine Prompt
                user_text = prompt_text
                if not user_text:
                    user_text = "Analyze the screen. If you see combat, give tactics. If loot, value it."

                # C. AI Request (Blocking call)
                logging.debug("Pipeline: Sending to AI...")
                response = ai.analyze_image(img, user_text, self.history)
                logging.debug("Pipeline: Response received.")

                # D. Success -> Update UI on Main Thread
                # We schedule the success handler. It will handle unlocking the UI.
                self.after(0, lambda: self._handle_success(user_text, response))

            except Exception as e:
                logging.error(f"Pipeline Error: {e}", exc_info=True)
                self.after(0, lambda err=str(e): self._handle_error(err))

        threading.Thread(target=task, daemon=True).start()

    def _toggle_loading_state(self, is_loading):
        """Locks UI during processing and shows/hides a 'Thinking...' indicator."""
        if is_loading:
            # LOCK INPUT
            self.prompt_entry.configure(state="disabled", placeholder_text="Proxi is thinking...")

            # SHOW INDICATOR
            self.text_area.configure(state="normal")
            self.loading_start_index = self.text_area.index("insert") # Remember start pos
            self.text_area.insert("end", "\nProxi: ...", "ai_tag")
            self.text_area.see("end")
            self.text_area.configure(state="disabled")

            self.update_idletasks()
        else:
            # UNLOCK INPUT
            self.prompt_entry.configure(state="normal", placeholder_text="Ask a question... (or press F11)")
            self.prompt_entry.focus()

            # REMOVE INDICATOR
            if hasattr(self, 'loading_start_index'):
                self.text_area.configure(state="normal")
                # Remove the "..." text we added
                self.text_area.delete(self.loading_start_index, "end")
                self.text_area.configure(state="disabled")

    def _handle_success(self, user_text, response):
        logging.debug("UI: Handling success.")

        # 1. CLEANUP FIRST (Remove "Thinking..." dots)
        self._toggle_loading_state(False)

        # 2. THEN Update Status and Write Text
        self.set_status("Ready", "green")

        self.history.append({"role": "user", "text": user_text})
        self.history.append({"role": "model", "text": response})

        self.append_to_chat("Proxi", response)

    def _handle_error(self, error_msg):
        logging.debug(f"UI: Handling error -> {error_msg}")

        # 1. CLEANUP FIRST
        self._toggle_loading_state(False)

        self.set_status("Error", "red")
        self.append_to_chat("System", f"Error: {error_msg}")

    def append_to_chat(self, sender, text, clear=False):
        self.text_area.config(state="normal")
        if clear: self.text_area.delete("1.0", "end")

        if text is None:
            text = "(No response from AI)"

        if sender:
            self.text_area.insert("end", f"\n{sender}: ", "user_tag" if sender == "You" else "ai_tag")

        # Basic Markdown Parsing
        clean_text = str(text).replace("```markdown", "").replace("```", "").strip()

        for line in clean_text.split("\n"):
            line = line.strip()
            if not line: continue

            if line.startswith("#"):
                # Headers
                self.text_area.insert("end", line.lstrip("#").strip() + "\n", "header")
            elif line.startswith(("* ", "- ")):
                # Bullet points
                self.text_area.insert("end", " • ", "bullet")
                self._insert_bold(line[2:] + "\n")
            else:
                self._insert_bold(line + "\n")

        self.text_area.see("end")
        self.text_area.config(state="disabled")

    def _insert_bold(self, text):
        """Helper to parse **bold** text and apply tags."""
        parts = text.split("**")
        for i, part in enumerate(parts):
            tag = "bold" if i % 2 else "normal"
            self.text_area.insert("end", part, tag)

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
            logging.debug("System: Hotkeys registered.")
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
            # Bind right click to trigger update
            self.text_area.bind("<Button-3>", lambda e: self.perform_update(url))
            self.append_to_chat("System", f"Update {ver} available! Right-click here to install.")

    def perform_update(self, url):
        self.text_area.unbind("<Button-3>")
        self.append_to_chat("System", "⏳ Downloading update... The app will restart automatically.")
        threading.Thread(target=updater.update_app, args=(url,), daemon=True).start()

    # --- Dev Tools ---
    def add_debug_controls(self):
        debug_frame = ctk.CTkFrame(self.main_container, height=30, fg_color="#333333")
        debug_frame.pack(side="bottom", fill="x")

        ctk.CTkButton(debug_frame, text="Dump", width=60, height=20, fg_color="#444",
                      command=self.debug_save).pack(side="left", padx=5)
        ctk.CTkButton(debug_frame, text="Mock", width=60, height=20, fg_color="#444",
                      command=self.debug_load).pack(side="left", padx=5)

    def debug_save(self):
        try:
            capture.capture_screen().save("debug.png")
            if platform.system() == "Darwin": os.system("open debug.png")
            else: os.system("start debug.png")
            logging.debug("Dev: Dumped debug.png")
        except Exception as e:
            logging.error(f"Debug dump failed: {e}")

    def debug_load(self):
        logging.debug("Dev: Mock load triggered.")
        threading.Thread(target=self._run_ai_pipeline, args=(self.prompt_entry.get() or None,), daemon=True).start()