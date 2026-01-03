import os
import sys
import requests
import webbrowser
import subprocess
import platform

# --- CONFIGURATION ---
REPO_OWNER = "bykowskiolaf"
REPO_NAME = "ai-game-helper"

def get_version():
    """Reads the version.txt file embedded inside the EXE"""
    try:
        # If running as compiled exe, look in the temporary MEIPASS folder
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
            
        version_path = os.path.join(base_path, 'version.txt')
        
        if os.path.exists(version_path):
            with open(version_path, 'r') as f:
                return f.read().strip()
    except Exception:
        pass
        
    return "0.0.0" # Default if running from source/dev

CURRENT_VERSION = get_version()

def check_for_updates():
    """
    Checks GitHub Releases for a newer version.
    Returns (update_available: bool, download_url: str, new_version: str)
    """
    try:
        print(f"Checking updates... Current: {CURRENT_VERSION}")
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        
        data = response.json()
        latest_tag = data["tag_name"].strip()  # e.g., "1.0.5" or "v1.0.5"
        
        # Clean versions for comparison (remove 'v')
        latest_clean = latest_tag.lstrip("v")
        current_clean = CURRENT_VERSION.lstrip("v")
        
        if latest_clean != current_clean:
            # Find the .exe asset
            for asset in data["assets"]:
                if asset["name"].endswith(".exe"):
                    return True, asset["browser_download_url"], latest_tag
                    
    except Exception as e:
        print(f"Update check failed: {e}")
        
    return False, None, None

def update_app(download_url):
    """
    Downloads the new exe, replaces the current one, and restarts.
    """
    # On Mac/Linux, we just open the browser (auto-replace is hard on Mac)
    if platform.system() != "Windows":
        webbrowser.open(download_url)
        return

    try:
        # 1. Download new file
        print("Downloading update...")
        response = requests.get(download_url, stream=True)
        new_exe_name = "ESO-Helper-New.exe"
        
        with open(new_exe_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Rename current running exe to .old 
        # (Windows allows renaming running executables, but not deleting them)
        current_exe = sys.executable
        old_exe = current_exe + ".old"
        
        if os.path.exists(old_exe):
            try:
                os.remove(old_exe) # Try to clean up previous update mess
            except:
                pass 
            
        os.rename(current_exe, old_exe)
        
        # 3. Rename new downloaded file to the original name
        os.rename(new_exe_name, current_exe)
        
        # 4. Restart the app
        print("Restarting...")
        subprocess.Popen([current_exe])
        sys.exit(0)

    except Exception as e:
        print(f"Update failed: {e}")
        # Fallback: Open browser so user can download manually
        webbrowser.open(download_url)