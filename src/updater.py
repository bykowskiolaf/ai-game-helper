import os
import sys
import requests
import webbrowser
import subprocess
import platform
import logging
from packaging.version import parse as parse_version
from config import REPO_OWNER, REPO_NAME

def get_version():
    try:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        with open(os.path.join(base_path, 'version.txt'), 'r') as f:
            return f.read().strip()
    except:
        return "0.0.0"

CURRENT_VERSION = get_version()

def check_for_updates():
    try:
        logging.info(f"Checking for updates... Current: {CURRENT_VERSION}")
        
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200: 
            logging.error(f"GitHub API Error: {response.status_code}")
            return False, None, None, f"API Error {response.status_code}"
        
        releases = response.json()
        current_ver = parse_version(CURRENT_VERSION)
        allow_pre = current_ver.is_prerelease

        best_release = None
        best_ver = parse_version("0.0.0")

        for release in releases:
            r_ver = parse_version(release["tag_name"])
            if not allow_pre and r_ver.is_prerelease: continue
            if r_ver > best_ver:
                best_ver = r_ver
                best_release = release

        if best_release and best_ver > current_ver:
            logging.info(f"New update found: {best_release['tag_name']}")
            for asset in best_release["assets"]:
                if asset["name"].endswith(".exe"):
                    return True, asset["browser_download_url"], best_release["tag_name"], "Update found"
            
            logging.warning("Update exists but has no .exe asset")
            return False, None, None, "No EXE found"

        logging.info("App is up to date.")
        return False, None, None, "Up to date"
    except Exception as e:
        logging.exception("Update check failed")
        return False, None, None, str(e)

def update_app(download_url):
    if platform.system() != "Windows":
        webbrowser.open(download_url)
        return

    try:
        logging.info(f"Starting download from: {download_url}")
        
        # 1. Download
        response = requests.get(download_url, stream=True)
        new_exe = "Update.exe"
        with open(new_exe, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info("Download complete. Swapping files...")

        # 2. Swap and Restart
        current_exe = sys.executable
        old_exe = current_exe + ".old"
        
        if os.path.exists(old_exe):
            try: os.remove(old_exe)
            except: pass 
            
        os.rename(current_exe, old_exe)
        os.rename(new_exe, current_exe)
        
        logging.info("Restarting application...")
        
        # 3. Launch Detached Process
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen([current_exe], creationflags=DETACHED_PROCESS, shell=False)
        sys.exit(0)

    except Exception as e:
        logging.error(f"Update failed: {e}")
        webbrowser.open(download_url)