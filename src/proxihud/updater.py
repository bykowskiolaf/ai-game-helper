import os
import sys
import requests
import webbrowser
import subprocess
import platform
import logging
import time
from packaging.version import parse as parse_version
from .config import REPO_OWNER, REPO_NAME, is_dev

def get_version():
    try:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            v_file = os.path.join(base_path, 'proxihud', 'version.txt')
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            v_file = os.path.join(base_path, 'version.txt')

        if os.path.exists(v_file):
            with open(v_file, 'r') as f:
                return f.read().strip()
        return "0.0.0"
    except Exception as e:
        return f"Err: {e}"

CURRENT_VERSION = get_version()

def check_for_updates():
    try:
        if is_dev():
            logging.info("Dev Mode detected, skipping update check.")
            return False, None, None, "Dev Mode"

        logging.info(f"Checking for updates... Local: {CURRENT_VERSION}")

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return False, None, None, f"API Error {response.status_code}"

        releases = response.json()
        current_ver = parse_version(CURRENT_VERSION)

        allow_pre = current_ver.is_prerelease

        best_release = None
        best_ver = parse_version("0.0.0")

        for release in releases:
            try:
                r_ver = parse_version(release["tag_name"])
                if not allow_pre and r_ver.is_prerelease: continue

                if r_ver > best_ver:
                    best_ver = r_ver
                    best_release = release
            except: continue

        if best_release and best_ver > current_ver:
            logging.info(f"Update available: {best_release['tag_name']}")
            for asset in best_release["assets"]:
                if asset["name"].endswith(".exe"):
                    return True, asset["browser_download_url"], best_release["tag_name"], "Update found"

            return False, None, None, "No EXE found"

        return False, None, None, "Up to date"
    except Exception as e:
        logging.exception("Update check failed")
        return False, None, None, str(e)

def update_app(download_url):
    if platform.system() != "Windows":
        webbrowser.open(download_url)
        return

    try:
        logging.info(f"Downloading update from: {download_url}")

        # 1. Download to temp file
        response = requests.get(download_url, stream=True)
        new_exe = "Update.tmp.exe"
        with open(new_exe, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info("Download finished. preparing to swap.")

        # 2. Rename Logic
        current_exe = sys.executable
        old_exe = current_exe + ".old"

        # Clean up previous update mess if it exists
        if os.path.exists(old_exe):
            try: os.remove(old_exe)
            except: pass

            # 3. The Swap
        os.rename(current_exe, old_exe)
        os.rename(new_exe, current_exe)

        logging.info("Files swapped. Launching new process...")

        # Give the filesystem a moment to unlock the file handle
        time.sleep(1.0)

        # 4. Launch using Windows Shell
        # os.startfile is "Fire and Forget" - exactly like double-clicking the EXE.
        os.startfile(current_exe)

        # 5. HARD KILL SELF
        logging.info("Exiting...")
        os._exit(0)

    except Exception as e:
        logging.error(f"Update failed: {e}")
        # If it failed, try to restore
        try:
            if os.path.exists("Update.tmp.exe"): os.remove("Update.tmp.exe")
        except: pass