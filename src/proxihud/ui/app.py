import customtkinter as ctk
import threading
import sys
import logging
import platform

from .. import config, capture, ai, updater, utils
from .window import DraggableWindow
from .settings import SettingsDialog
from .startup import StartupWizard
from .chat import ChatDisplay

class GameHelperApp(DraggableWindow):
    def __init__(self):
        super().__init__()
        self.title(config.APP_NAME)
        self._setup_window_properties()

        # State
        self.history = []
        self.settings = config.load_settings()

        # Layout
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # Wizard checks API keys before showing HUD
        self.wizard = StartupWizard(self.main_container, self.launch_hud)
        self.wizard.start()

    def _setup_window_properties(self):
        try: self.iconbitmap(config.resource_path("icon.ico"))
        except: pass

        geo = config.load_settings().get("geometry", "500x300+50+50")
        try: self.geometry(geo)
        except: self.geometry("500x300+50+50")

        self.configure(fg_color="#1a1a1a")
        self.attributes("-topmost", True)
        self.attributes("-alpha", config.load_settings().get("opacity", 0.9))
        self.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.bind('<ButtonRelease-1>', self.save_geometry)

    def launch_hud(self):
        """Builds the main UI."""
        for widget in self.main_container.winfo_children(): widget.destroy()
        self.overrideredirect(True)

        # --- 1. Input Bar (Bottom) ---
        # PACK FIRST (Reserves bottom space)
        self.prompt_frame = ctk.CTkFrame(self.main_container, height=40, fg_color="#202020", corner_radius=8)
        self.prompt_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        self.prompt_frame.bind('<Button-1>', self.clickwin)
        self.prompt_frame.bind('<B1-Motion>', self.dragwin)

        # Settings Button
        ctk.CTkButton(self.prompt_frame, text="⚙️", width=30, fg_color="transparent", hover_color="#333",
                      font=("Segoe UI", 14), command=self.open_settings).pack(side="left", padx=(5, 0))

        # Input Entry
        self.prompt_entry = ctk.CTkEntry(self.prompt_frame, placeholder_text="Ask...", font=("Segoe UI", 12),
                                         border_width=0, fg_color="transparent", text_color="#eee", height=30)
        self.prompt_entry.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.prompt_entry.bind("<Return>", self.trigger_chat)

        # FIX: FORCE FOCUS ON CLICK
        # This tells Windows: "Hey, I know I'm borderless, but give me the keyboard."
        def force_focus(event):
            self.prompt_entry.focus_force()
        self.prompt_entry.bind("<Button-1>", force_focus)

        # Resize Grip
        self.resize_grip = ctk.CTkLabel(self.prompt_frame, text="↘", font=("Arial", 14), text_color="#555", cursor="sizing", width=20)
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)
        self.resize_grip.bind("<ButtonRelease-1>", self.save_geometry)

        # --- 2. Chat Area (Top) ---
        # PACK SECOND (Takes remaining space)
        self.chat_container = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a")
        self.chat_container.pack(fill="both", expand=True, padx=2, pady=(2, 0))

        self.chat = ChatDisplay(self.chat_container)
        self.chat.pack(fill="both", expand=True)

        # Bind dragging to the chat area
        self.chat.text_widget.bind('<Button-1>', self.clickwin)
        self.chat.text_widget.bind('<B1-Motion>', self.dragwin)

        # Init
        ver = "Dev" if config.is_dev() else updater.CURRENT_VERSION
        self.chat.append("System", f"ProxiHUD Ready ({ver})\n[F11] Scan | [Enter] Chat")

        if config.is_dev(): self.add_debug_controls()
        if capture.is_windows(): self.start_hotkeys()
        threading.Thread(target=self._bg_update_check, daemon=True).start()

    # --- Logic ---

    def set_status(self, color):
        """Visual feedback via prompt frame color."""
        cols = {"orange": "#B45309", "red": "#7F1D1D", "green": "#202020"}
        self.prompt_frame.configure(fg_color=cols.get(color, "#202020"))
        self.update_idletasks()

    def toggle_loading(self, active):
        if active:
            self.prompt_entry.configure(state="disabled", placeholder_text="Thinking...")
            self.chat.show_loading()
        else:
            self.prompt_entry.configure(state="normal", placeholder_text="Ask...")
            self.prompt_entry.focus()
            self.chat.hide_loading()
        self.update_idletasks()

    def trigger_scan(self):
        logging.debug("Hotkey Triggered")
        self.history = []
        self.chat.append("System", "Scanning screen...", clear=True)
        threading.Thread(target=self._pipeline, args=(None,), daemon=True).start()

    def trigger_chat(self, event):
        text = self.prompt_entry.get().strip()
        if not text: return
        self.prompt_entry.delete(0, 'end')
        self.chat.append("You", text)
        self.history.append({"role": "user", "text": text})
        threading.Thread(target=self._pipeline, args=(text,), daemon=True).start()

    def _pipeline(self, prompt_text):
        """Background thread AI logic."""
        self.set_status("orange")
        self.toggle_loading(True)

        def task():
            try:
                img = capture.capture_screen()
                user_text = prompt_text or "Analyze screen. Combat tactics or loot value."

                resp = ai.analyze_image(img, user_text, self.history)

                # Update UI on Main Thread
                self.after(0, lambda: self._on_success(user_text, resp))
            except Exception as e:
                logging.error(e, exc_info=True)
                self.after(0, lambda err=str(e): self._on_error(err))

        threading.Thread(target=task, daemon=True).start()

    def _on_success(self, prompt, response):
        self.toggle_loading(False)
        self.set_status("green")

        self.history.append({"role": "user", "text": prompt})
        self.history.append({"role": "model", "text": response})
        self.chat.append("Proxi", response)

    def _on_error(self, msg):
        self.toggle_loading(False)
        self.set_status("red")
        self.chat.append("System", f"Error: {msg}")

    # --- Utils ---
    def start_resize(self, e):
        self._rx, self._ry, self._rw = e.x_root, e.y_root, self.winfo_width()
        return "break"
    def perform_resize(self, e):
        self.geometry(f"{max(350, self._rw + (e.x_root - self._rx))}x{self.winfo_height()}")
        return "break"
    def save_geometry(self, e=None):
        config.save_settings({**self.settings, "geometry": self.geometry()})

    def open_settings(self):
        SettingsDialog(self, self.settings, self._apply_settings)
    def _apply_settings(self, new_s):
        self.settings = new_s
        self.attributes("-alpha", new_s["opacity"])
        config.save_settings(new_s)

    def start_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(self.settings.get("hotkey_trigger", "f11"), self.trigger_scan)
            keyboard.add_hotkey(self.settings.get("hotkey_exit", "f12"), self.quit_app)
        except: pass

    def quit_app(self):
        self.save_geometry()
        self.quit()
        sys.exit()

    def _bg_update_check(self):
        avail, url, ver, _ = updater.check_for_updates()
        if avail:
            self.chat.text_widget.bind("<Button-3>", lambda e: threading.Thread(target=updater.update_app, args=(url,)).start())
            self.chat.append("System", f"Update {ver} available! Right-click to update.")

    def add_debug_controls(self):
        debug_frame = ctk.CTkFrame(self.main_container, height=20, fg_color="#333")
        debug_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(debug_frame, text="Dump", width=50, height=18, fg_color="#444",
                      command=lambda: capture.capture_screen().save("debug.png")).pack(side="left", padx=5)