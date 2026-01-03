import customtkinter as ctk
import threading
import config
import capture
import ai

class GameHelperApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ESO Helper")
        self.geometry("400x600")
        
        # --- OVERLAY SETTINGS ---
        self.attributes("-topmost", True)  # Always on top
        self.attributes("-alpha", 0.85)    # 85% Opacity (See-through!)
        ctk.set_appearance_mode("Dark")
        
        # Check if we need to ask for a key
        if not config.get_api_key():
            self.show_login_screen()
        else:
            self.show_main_screen()

    def show_login_screen(self):
        """Screen 1: Ask for API Key"""
        self.clear_window()
        self.attributes("-alpha", 1.0) # Solid window for login
        
        ctk.CTkLabel(self, text="🔑 Enter Google API Key", font=("Arial", 16, "bold")).pack(pady=(50, 10))
        
        self.key_entry = ctk.CTkEntry(self, width=300, placeholder_text="Paste key here...")
        self.key_entry.pack(pady=10)

        ctk.CTkButton(self, text="Save & Start", command=self.save_key).pack(pady=10)
        ctk.CTkLabel(self, text="Saved locally in .env", text_color="gray").pack(pady=20)

    def save_key(self):
        key = self.key_entry.get().strip()
        if len(key) > 5:
            config.save_api_key(key)
            self.show_main_screen()

    def show_main_screen(self):
        """Screen 2: The Main App"""
        self.clear_window()
        self.attributes("-alpha", 0.85) # Back to transparent mode

        # Header
        ctk.CTkLabel(self, text="ESO Companion", font=("Arial", 20, "bold")).pack(pady=10)
        
        # Status
        hotkey_text = "Press Ctrl+Alt+Z" if capture.is_windows() else "Click Capture Button"
        self.status_label = ctk.CTkLabel(self, text=f"Ready. {hotkey_text}", text_color="gray")
        self.status_label.pack(pady=5)

        # Button
        ctk.CTkButton(self, text="📸 Capture & Analyze", command=self.run_analysis_thread, height=40, fg_color="#1a73e8").pack(pady=10)

        # Text Area (Slightly more opaque for readability)
        self.textbox = ctk.CTkTextbox(self, width=380, height=400, wrap="word", fg_color="#2b2b2b")
        self.textbox.pack(padx=10, pady=10)
        self.textbox.insert("0.0", "Waiting for command...")
        
        # Opacity Slider (Optional cool feature)
        self.slider = ctk.CTkSlider(self, from_=0.2, to=1.0, command=self.change_opacity)
        self.slider.set(0.85)
        self.slider.pack(pady=10)
        ctk.CTkLabel(self, text="Opacity", font=("Arial", 10)).pack()

        # Start Hotkeys (Windows Only)
        if capture.is_windows():
            self.start_hotkeys()

    def change_opacity(self, value):
        self.attributes("-alpha", value)

    def run_analysis_thread(self):
        """Runs logic in background to keep UI responsive"""
        t = threading.Thread(target=self.run_logic, daemon=True)
        t.start()

    def run_logic(self):
        self.update_text("📸 Capturing...")
        
        try:
            # 1. Capture
            img = capture.capture_screen()
            img.thumbnail((1024, 1024)) # Resize for speed

            # 2. Analyze
            self.update_text("🧠 Analyzing...")
            result = ai.analyze_image(img)
            
            # 3. Show
            self.update_text(result)
            self.status_label.configure(text="✅ Done")

        except Exception as e:
            self.update_text(f"Error: {e}")

    def update_text(self, text):
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", text)

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def start_hotkeys(self):
        """Safe Windows hotkey listener"""
        try:
            import keyboard
            def listen():
                keyboard.add_hotkey("ctrl+alt+z", self.run_analysis_thread)
                keyboard.wait()
            threading.Thread(target=listen, daemon=True).start()
        except ImportError:
            print("Keyboard library not found (okay if on Mac)")