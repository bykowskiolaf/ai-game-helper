import customtkinter as ctk
import tkinter as tk

class ChatDisplay(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        # The Text Widget
        self.text_widget = tk.Text(
            self,
            bg="#1a1a1a",
            fg="#e0e0e0",
            font=("Consolas", 11),
            wrap="word",
            bd=0,
            highlightthickness=0,
            padx=10,
            pady=10,
            cursor="arrow"
        )
        self.text_widget.pack(fill="both", expand=True)

        self._configure_tags()
        self.loading_mark = None

    def _configure_tags(self):
        # Adjusted spacing to be tighter but readable
        self.text_widget.tag_config("user_tag", foreground="#4cc9f0", font=("Segoe UI", 11, "bold"), spacing1=10, spacing3=2)
        self.text_widget.tag_config("ai_tag", foreground="#f72585", font=("Segoe UI", 11, "bold"), spacing1=10, spacing3=2)
        self.text_widget.tag_config("system_tag", foreground="#ffd60a", font=("Consolas", 11, "bold"), spacing1=10, spacing3=2)

        # Body text
        self.text_widget.tag_config("normal", font=("Consolas", 11), foreground="#e0e0e0", spacing2=2)
        self.text_widget.tag_config("bold", font=("Consolas", 11, "bold"), foreground="#ffffff", spacing2=2)

        # Markdown elements
        self.text_widget.tag_config("header", font=("Consolas", 13, "bold"), foreground="#ffd60a", spacing1=5, spacing3=2)
        self.text_widget.tag_config("bullet", foreground="#ffd60a", font=("Consolas", 11, "bold"), lmargin1=15, lmargin2=25, spacing2=2)

    def append(self, sender, text, clear=False):
        self.text_widget.config(state="normal")
        if clear:
            self.text_widget.delete("1.0", "end")

        if text is None: text = "(No response)"

        # Determine tag based on sender
        tag = "system_tag"
        if sender == "You": tag = "user_tag"
        elif sender == "Proxi": tag = "ai_tag"

        if sender:
            self.text_widget.insert("end", f"\n{sender}: ", tag)

        # Parse Markdown-ish text
        clean_text = str(text).replace("```markdown", "").replace("```", "").strip()

        for line in clean_text.split("\n"):
            line = line.strip()
            if not line: continue

            if line.startswith("#"):
                self.text_widget.insert("end", line.lstrip("#").strip() + "\n", "header")
            elif line.startswith(("* ", "- ")):
                self.text_widget.insert("end", " • ", "bullet")
                self._insert_bold(line[2:] + "\n")
            else:
                self._insert_bold(line + "\n")

        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def _insert_bold(self, text):
        parts = text.split("**")
        for i, part in enumerate(parts):
            tag = "bold" if i % 2 else "normal"
            self.text_widget.insert("end", part, tag)

    def show_loading(self):
        """Shows the three dots."""
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", "\nProxi: ...", "ai_tag")
        self.loading_mark = self.text_widget.index("end-2l") # Mark position
        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def hide_loading(self):
        """Removes the three dots."""
        self.text_widget.config(state="normal")
        # Search for the specific string at the end to delete safely
        last_line = self.text_widget.get("end-2c linestart", "end-1c")
        if "..." in last_line:
            self.text_widget.delete("end-2c linestart", "end")
        self.text_widget.config(state="disabled")