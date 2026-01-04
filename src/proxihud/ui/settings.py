import customtkinter as ctk
from .. import config
from .components import ApiKeyRow

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_settings, apply_callback):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("340x550")
        self.attributes("-topmost", True)
        self.apply_callback = apply_callback
        self.settings = current_settings.copy()
        self.key_rows = []

        # Scroll Container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.setup_ui()

    def setup_ui(self):
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

        # 3. API Keys
        self.add_header("🔑 API Keys")
        self.keys_container = ctk.CTkFrame(self.scroll, fg_color="#2b2b2b", corner_radius=6)
        self.keys_container.pack(fill="x", padx=10, pady=5)
        
        # Load existing keys
        current_keys = config.get_api_keys()
        if not current_keys:
            self.add_key_row("")
        else:
            for k in current_keys:
                self.add_key_row(k)

        ctk.CTkButton(
            self.scroll, text="➕ Add Key", 
            fg_color="#333", hover_color="#444", 
            command=lambda: self.add_key_row("")
        ).pack(fill="x", padx=10, pady=5)

        # 4. Hotkeys
        self.add_header("⌨️ Hotkeys (Restart to apply)")
        self.trigger_entry = ctk.CTkEntry(self.scroll, placeholder_text="Trigger (e.g. f11)")
        self.trigger_entry.insert(0, self.settings.get("hotkey_trigger", "f11"))
        self.trigger_entry.pack(fill="x", padx=10, pady=2)
        
        # Save Button
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
        
        valid_keys = []
        for row in self.key_rows:
            k = row.get_key()
            if k and len(k) > 5: valid_keys.append(k)
        
        config.save_api_key(",".join(valid_keys))
        self.apply_callback(self.settings)
        self.destroy()