import customtkinter as ctk

class ApiKeyRow(ctk.CTkFrame):
    def __init__(self, parent, key_text, remove_callback):
        super().__init__(parent, fg_color="transparent")
        self.pack(fill="x", pady=2)
        
        # Entry (Masked by default)
        self.entry = ctk.CTkEntry(self, show="*", height=28)
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
        self.entry.configure(show="" if self.visible else "*")
        self.eye_btn.configure(fg_color="#555" if self.visible else "#333")

    def get_key(self):
        return self.entry.get().strip()