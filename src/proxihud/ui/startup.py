import customtkinter as ctk
import os
import threading
from .. import config, installer

class StartupWizard:
    """
    Handles the initial setup flow:
    1. Check/Enter API Keys
    2. Check/Install Addon
    """
    def __init__(self, parent_container, on_complete_callback):
        self.container = parent_container
        self.on_complete = on_complete_callback

    def start(self):
        # State Machine Logic
        if not config.get_api_keys():
            self.show_step_1_apikey()
        elif not installer.is_installed():
            self.show_step_2_addon()
        else:
            self.on_complete()

    def clear_view(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_step_1_apikey(self):
        self.clear_view()
        # Ensure parent window size accommodates this view
        self.container.master.geometry("400x300")

        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(content, text="Step 1 of 2", text_color="#f72585", font=("Segoe UI", 12, "bold")).pack()
        ctk.CTkLabel(content, text="Connect Intelligence", font=("Segoe UI", 18, "bold")).pack(pady=(0, 10))

        msg = "ProxiHUD needs a Google Gemini API Key to see\nand analyze your game."
        ctk.CTkLabel(content, text=msg, font=("Segoe UI", 12), text_color="gray").pack(pady=(0, 15))

        self.api_entry = ctk.CTkEntry(content, width=300, placeholder_text="Paste API Key here...")
        self.api_entry.pack(pady=5)
        self.api_entry.bind("<Return>", self._submit_key)

        ctk.CTkButton(content, text="Next ➜", width=300, command=lambda: self._submit_key(None)).pack(pady=10)

        link = ctk.CTkLabel(content, text="(Get a free key here)", text_color="#4cc9f0", cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: os.system("start https://aistudio.google.com/app/apikey"))

    def _submit_key(self, event):
        key = self.api_entry.get().strip()
        if len(key) > 10: # Basic validation
            config.save_api_key(key)
            self.start() # Re-evaluate state

    def show_step_2_addon(self):
        self.clear_view()
        self.container.master.geometry("400x350")

        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(content, text="Step 2 of 2", text_color="#f72585", font=("Segoe UI", 12, "bold")).pack()
        ctk.CTkLabel(content, text="Connect Game Data", font=("Segoe UI", 18, "bold")).pack(pady=(0, 10))

        msg = f"We will install a bridge AddOn to:\n{config.get_eso_addon_path()}"
        ctk.CTkLabel(content, text=msg, font=("Segoe UI", 12), text_color="gray").pack(pady=(0, 20))

        self.install_btn = ctk.CTkButton(content, text="Install Bridge AddOn", width=300, fg_color="#2ecc71",
                                         hover_color="#27ae60", command=self._run_install)
        self.install_btn.pack(pady=5)

        ctk.CTkButton(content, text="Skip (Reduced Functionality)", width=300, fg_color="transparent",
                      border_width=1, command=self.on_complete).pack(pady=5)

    def _run_install(self):
        self.install_btn.configure(text="Installing...", state="disabled")

        def _thread_target():
            success = installer.install_addon()
            if success:
                self.container.after(0, self.on_complete)
            else:
                self.container.after(0, lambda: self.install_btn.configure(text="Error. Try Manually?", fg_color="#e74c3c"))

        threading.Thread(target=_thread_target, daemon=True).start()