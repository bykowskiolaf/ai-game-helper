import platform
import subprocess
from PIL import Image, ImageGrab

def is_windows():
    return platform.system() == "Windows"

def capture_screen():
    """
    Captures the primary screen in-memory.
    - Windows: Uses 'mss' (extremely fast for games).
    - Mac: Uses 'ImageGrab' (native, stable, no files).
    """
    if is_windows():
        # Windows: MSS is optimized for high-FPS capturing
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    else:
        return ImageGrab.grab()