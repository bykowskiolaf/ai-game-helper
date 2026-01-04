import platform
import logging
from PIL import Image, ImageGrab

def is_windows():
    return platform.system() == "Windows"

def capture_screen():
    """
    Captures the primary screen.
    - Windows: Uses 'mss' (Fast, DirectX/OpenGL compatible).
    - Mac/Linux: Uses 'ImageGrab'.
    """
    if is_windows():
        import mss
        try:
            with mss.mss() as sct:
                # sct.monitors[0] is 'All Monitors' combined
                # sct.monitors[1] is usually 'Primary'
                # We try 1, fall back to 0 if single monitor setup
                monitor_idx = 1 if len(sct.monitors) > 1 else 0
                monitor = sct.monitors[monitor_idx]

                sct_img = sct.grab(monitor)
                return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception as e:
            logging.error(f"MSS Capture failed: {e}. Falling back to ImageGrab.")
            return ImageGrab.grab()
    else:
        return ImageGrab.grab()