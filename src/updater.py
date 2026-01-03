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
        if getattr(sys, 'frozen', False):
            # If running as compiled exe, look in the temporary MEIPASS folder
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
            
        version_path = os.path.join(base_path, 'version.txt')
        
        if os.path.exists(version_path):
            with open(version_path, 'r') as f:
                return f.read().strip()
    except Exception:
        pass
    return "0.0.0" # Default for dev mode

CURRENT_VERSION = get_version()

def check_for_updates():
    """
    Checks GitHub Releases.
    Returns: (is_available, url, version, status_message)
    """
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 404:
            return False, None, None, "❌ Error: Repo not found (Private?)"
        if response.status_code == 403:
            return False, None, None, "❌ Error: API Rate Limit Exceeded"
            
        response.raise_for_status()
        
        data = response.json()
        latest_tag = data["tag_name"].strip()  # e.g. "v1.0.5"
        
        # Clean versions (remove 'v')
        latest_clean = latest_tag.lstrip("v")
        current_clean = CURRENT_VERSION.lstrip("v")
        
        if latest_clean != current_clean:
            # Find the .exe asset
            for asset in data["assets"]:
                if asset["name"].endswith(".exe"):
                    return True, asset["browser_download_url"], latest_tag, f"Update found: {latest_tag}"
            return False, None, None, f"Update found ({latest_tag}) but no .exe asset!"
            
        return False, None, None, f"Up to date ({CURRENT_VERSION})"

    except Exception as e:
        return False, None, None, f"Check Failed: {str(e)}"

def update_app(download_url):
    """Downloads and restarts the app"""
    if platform.system() != "Windows":
        webbrowser.open(download_url)
        return

    try:
        # 1. Download
        response = requests.get(download_url, stream=True)
        new_exe_name = "ESO-Helper-New.exe"
        with open(new_exe_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Swap Files
        current_exe = sys.executable
        old_exe = current_exe + ".old"
        
        if os.path.exists(old_exe):
            try: os.remove(old_exe)
            except: pass 
            
        os.rename(current_exe, old_exe)
        os.rename(new_exe_name, current_exe)
        
        # 3. Restart
        subprocess.Popen([current_exe])
        sys.exit(0)

    except Exception as e:
        webbrowser.open(download_url)