import os
import sys
import requests
import webbrowser
import subprocess
import platform
from packaging.version import parse as parse_version

# --- CONFIGURATION ---
REPO_OWNER = "bykowskiolaf"
REPO_NAME = "ai-game-helper"

def get_version():
    """Reads the version.txt file embedded inside the EXE"""
    try:
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
    return "0.0.0"

CURRENT_VERSION = get_version()

def check_for_updates():
    """
    Smart Update Check:
    - If User is Stable: Look for newer Stable.
    - If User is Pre-release (RC/Alpha): Look for ANY newer version.
    """
    try:
        print(f"Checking updates... Current: {CURRENT_VERSION}")
        
        # We need the list of releases, not just 'latest' (which ignores pre-releases)
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return False, None, None, f"API Error: {response.status_code}"

        releases = response.json()
        if not releases:
            return False, None, None, "No releases found."

        current_ver = parse_version(CURRENT_VERSION)
        
        # Check if we are currently on a pre-release (e.g., 1.2.0rc1)
        am_i_nightly = current_ver.is_prerelease

        best_release = None
        best_ver = parse_version("0.0.0")

        for release in releases:
            tag_name = release["tag_name"]
            release_ver = parse_version(tag_name)

            # RULE 1: If I am Stable, ignore Pre-releases
            if not am_i_nightly and release_ver.is_prerelease:
                continue
            
            # RULE 2: Find the highest version number
            if release_ver > best_ver:
                best_ver = release_ver
                best_release = release

        # Compare found version vs current
        if best_release and best_ver > current_ver:
             # Find .exe
            for asset in best_release["assets"]:
                if asset["name"].endswith(".exe"):
                    return True, asset["browser_download_url"], best_release["tag_name"], f"New {best_release['tag_name']} available!"
            
            return False, None, None, f"Version {best_release['tag_name']} exists but has no EXE."

        return False, None, None, f"Up to date ({CURRENT_VERSION})"

    except Exception as e:
        return False, None, None, f"Check Failed: {str(e)}"

def update_app(download_url):
    """Downloads the new exe, replaces the current one, and restarts."""
    if platform.system() != "Windows":
        webbrowser.open(download_url)
        return

    try:
        # 1. Download new file
        print("Downloading update...")
        response = requests.get(download_url, stream=True)
        new_exe_name = "ESO-Helper-Update.exe"
        
        with open(new_exe_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Get paths
        current_exe = sys.executable
        old_exe = current_exe + ".old"
        
        # 3. Rename current running exe to .old 
        if os.path.exists(old_exe):
            try: os.remove(old_exe)
            except: pass 
            
        os.rename(current_exe, old_exe)
        
        # 4. Rename downloaded update to the original name
        os.rename(new_exe_name, current_exe)
        
        # 5. Restart cleanly
        print("Restarting...")
        
        # DETACHED_PROCESS flag ensures the new app isn't killed when this one dies
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen([current_exe], creationflags=DETACHED_PROCESS, shell=False)
        
        # 6. Kill self immediately
        sys.exit(0)

    except Exception as e:
        print(f"Update failed: {e}")
        # If auto-update fails, just open the browser
        webbrowser.open(download_url)