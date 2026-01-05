import sys
import os

# --- WINDOWS FIXES (PyInstaller) ---
# These are only needed when building/running on Windows.
if os.name == 'nt':
    try:
        import unicodedata
        import _overlapped
        import asyncio
    except ImportError:
        pass

# Ensure the current directory is in the path so we can import the package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from proxihud.main import main

if __name__ == "__main__":
    main()