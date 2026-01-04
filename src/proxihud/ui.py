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

        self.geometry("500x300+50+50") 
        self.configure(fg_color="#1a1a1a")
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.90) 
        self.lift() 
        self.enforce_topmost()

        # --- CHAT HISTORY STATE ---
        self.history = [] 

        if not config.get_api_key():
            self.show_login()
        else:
            self.show_hud()

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
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True)

        # 1. Debug (Bottom)
        if not getattr(sys, 'frozen', False):
            self.add_debug_controls()

        # 2. Input Bar (Above Debug)
        self.prompt_frame = ctk.CTkFrame(self.frame, height=30, fg_color="#2b2b2b")
        self.prompt_frame.pack(side="bottom", fill="x", padx=2, pady=2)
        
        self.prompt_entry = ctk.CTkEntry(
            self.prompt_frame, placeholder_text="Ask a follow-up question...",
            font=("Consolas", 11), border_width=0, fg_color="#333", text_color="#eee"
        )
        
        self.prompt_entry.pack(side="left", fill="both", expand=True, padx=(2, 25))
        self.prompt_entry.bind("<Return>", self.trigger_chat)
        
        # Focus Fix
        def on_entry_click(event):
            self.prompt_entry.focus_force()
            self.prompt_entry.focus_set()
            return "break"
        self.prompt_entry.bind("<Button-1>", on_entry_click)

        # 3. Text Area (Top)
        self.text_area = tk.Text(
            self.frame, bg="#1a1a1a", fg="#e0e0e0", 
            font=("Consolas", 11), wrap="word", bd=0, highlightthickness=0, padx=10, pady=10
        )
        self.text_area.pack(side="top", fill="both", expand=True)
        
        # Resize Grip
        self.resize_grip = ctk.CTkLabel(self.frame, text="↘", font=("Arial", 12), text_color="gray", cursor="sizing")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=0) 
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.perform_resize)

        # Styles
        self.text_area.tag_config("user_tag", foreground="#4cc9f0", font=("Consolas", 11, "bold"))
        self.text_area.tag_config("ai_tag", foreground="#f72585", font=("Consolas", 11, "bold"))
        self.text_area.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#ffffff")
        self.text_area.tag_config("header", font=("Consolas", 13, "bold"), foreground="#ffd60a")
        self.text_area.tag_config("bullet", foreground="#ffd60a")

        ver = updater.CURRENT_VERSION
        self.append_to_chat("System", f"ProxiHUD Ready ({ver})\n[F11] New Scan | [Type] Chat")

        # Bindings
        self.text_area.bind("<Button-3>", self.trigger_update_or_clear) 
        self.text_area.bind('<Button-1>', self.clickwin)
        self.text_area.bind('<B1-Motion>', self.dragwin)

        if capture.is_windows():
            self.start_hotkeys()

    def add_debug_controls(self):
        debug_frame = ctk.CTkFrame(self.frame, height=30, fg_color="#333333")
        debug_frame.pack(side="bottom", fill="x")
        ctk.CTkButton(debug_frame, text="Save Dump", width=80, height=20, fg_color="#444", command=self.debug_save).pack(side="left", padx=5)
        ctk.CTkButton(debug_frame, text="Load Mock", width=80, height=20, fg_color="#444", command=self.debug_load).pack(side="left", padx=5)

    # --- CHAT LOGIC ---

    def append_to_chat(self, sender, text, clear=False):
        """Adds a message to the UI log"""
        self.text_area.config(state="normal")
        if clear:
            self.text_area.delete("1.0", "end")
        
        if sender:
            tag = "user_tag" if sender == "You" else "ai_tag"
            self.text_area.insert("end", f"\n{sender}: ", tag)

        # Render Markdown logic
        clean_text = text.replace("```markdown", "").replace("```", "").strip()
        lines = clean_text.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith("#"):
                self.text_area.insert("end", line.lstrip("#").strip() + "\n", "header")
            elif line.startswith("* ") or line.startswith("- "):
                self.text_area.insert("end", " • ", "bullet")
                self._insert_bold(line[2:])
                self.text_area.insert("end", "\n")
            else:
                self._insert_bold(line)
                self.text_area.insert("end", "\n")

        self.text_area.see("end") 
        self.text_area.config(state="disabled")

    def _insert_bold(self, text):
        parts = text.split("**")
        for i, part in enumerate(parts):
            tag = "bold" if i % 2 == 1 else "normal"
            self.text_area.insert("end", part, tag)

    def trigger_scan(self):
        """F11: Starts a FRESH context (clears history)"""
        self.history = [] 
        self.append_to_chat("System", "Scanning...", clear=True)
        threading.Thread(target=self.run_logic, args=(None,), daemon=True).start()

    def trigger_chat(self, event):
        """Enter: Appends to CURRENT context"""
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
            
            # Call AI with History
            response = ai.analyze_image(img, user_text, self.history)
            
            self.history.append({"role": "model", "text": response})
            self.append_to_chat("Proxi", response)
            
        except Exception as e:
            self.append_to_chat("Error", str(e))

    # --- BOILERPLATE & DEBUG ---
    def start_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(config.TRIGGER_KEY, self.trigger_scan)
            keyboard.add_hotkey(config.EXIT_KEY, self.quit)
        except: pass

    def start_resize(self, e): self._rx, self._ry, self._rw = e.x_root, e.y_root, self.winfo_width()
    def perform_resize(self, e): 
        self.geometry(f"{max(350, self._rw + (e.x_root - self._rx))}x{self.winfo_height()}")
    
    def debug_save(self): 
        capture.capture_screen().save("debug.png"); os.system("start debug.png")
    def debug_load(self):
        if os.path.exists("mock.png"):
            user_text = self.prompt_entry.get().strip() or None
            self.append_to_chat("System", "Loaded Mock")
            threading.Thread(target=lambda: self.run_logic(user_text), daemon=True).start()

    def bg_update_check(self):
        import time; time.sleep(1)
        avail, url, ver, msg = updater.check_for_updates()
        if avail: 
            self.update_url = url; self.new_ver = ver
            self.append_to_chat("System", f"Update {ver} available. Right-click to install.")
            self.update_available = True

    def trigger_update_or_clear(self, e):
        if self.update_available:
            self.append_to_chat("System", f"⬇ Downloading {self.new_ver}...")
            # Run in thread so UI doesn't freeze, but log errors if it fails
            threading.Thread(target=self._run_update_thread, daemon=True).start()
        else:
            self.render_markdown(f"READY ({updater.CURRENT_VERSION})")

    def _run_update_thread(self):
        try:
            updater.update_app(self.update_url)
        except Exception as e:
            self.append_to_chat("System", f"Update Failed: {e}")