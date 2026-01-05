import sys
import os

# --- WINDOWS FIXES (PyInstaller) ---
if os.name == 'nt':
    try:
        import unicodedata
        import _overlapped
    except ImportError:
        pass

# --- PYINSTALLER ENVIRONMENT CLEANUP ---
# Fixes "Can't find init.tcl" when restarting/updating
if getattr(sys, 'frozen', False):
    current_mei = sys._MEIPASS

    # List of toxic variables that break Tkinter if inherited from an old process
    toxic_vars = ['TCL_LIBRARY', 'TK_LIBRARY', 'TIX_LIBRARY']

    for var in toxic_vars:
        path = os.environ.get(var)
        if path and current_mei not in path:
            # Found a path pointing to a DIFFERENT (old) temp folder. Nuke it.
            # Python will fall back to finding the correct internal folder.
            del os.environ[var]

# Ensure the current directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from proxihud.main import main

if __name__ == "__main__":
    main()