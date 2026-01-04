import customtkinter as ctk

class DraggableWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self._offsetx = 0
        self._offsety = 0

        # Bind events
        self.bind('<Button-1>', self.clickwin)
        self.bind('<B1-Motion>', self.dragwin)

    def clickwin(self, event):
        widget_name = str(event.widget).lower()

        # ONLY block dragging if clicking an actual Entry (typing) field.
        # We REMOVED "or 'text' in widget_name" so you can drag the log area.
        if "entry" in widget_name:
            return

        self._offsetx = event.x_root - self.winfo_x()
        self._offsety = event.y_root - self.winfo_y()

    def dragwin(self, event):
        widget_name = str(event.widget).lower()
        if "entry" in widget_name:
            return

        x = event.x_root - self._offsetx
        y = event.y_root - self._offsety
        self.geometry(f'+{x}+{y}')