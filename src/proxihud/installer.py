import os
import sys
import shutil
import logging
from . import config

def get_source_addon_path():
    """
    Finds the 'resources/addon/ProxiHUD_Bridge' folder.
    Handles both Dev environment and PyInstaller Frozen environment.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller: Resources are bundled into temp _MEIPASS folder
        base_path = sys._MEIPASS
        return os.path.join(base_path, "src", "proxihud", "resources", "addon", "ProxiHUD_Bridge")
    else:
        # Dev: Just look in the local folder structure relative to THIS file
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "resources", "addon", "ProxiHUD_Bridge"))

def is_installed():
    """Checks if the addon folder exists in the game Documents."""
    try:
        path = config.get_eso_addon_path()
        if not path: return False
        dest = os.path.join(path, "ProxiHUD_Bridge")

        # Check if the folder exists and has the manifest
        return os.path.exists(dest) and os.path.exists(os.path.join(dest, "ProxiHUD_Bridge.txt"))
    except:
        return False

def install_addon():
    """Copies the addon files from internal resources to the game folder."""
    try:
        # 1. Locate Source (Locally defined function, NOT config)
        source_dir = get_source_addon_path()

        if not os.path.exists(source_dir):
            logging.error(f"Installer Source not found at: {source_dir}")
            return False

        # 2. Locate Destination (From Config)
        eso_addons_path = config.get_eso_addon_path()
        if not os.path.exists(eso_addons_path):
            logging.warning(f"ESO AddOns folder not found at: {eso_addons_path}")
            return False

        dest_dir = os.path.join(eso_addons_path, "ProxiHUD_Bridge")

        # 3. Clean old installation
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)

            # 4. Copy new files
        shutil.copytree(source_dir, dest_dir)
        logging.info(f"Addon successfully installed to: {dest_dir}")
        return True

    except Exception as e:
        # This catches errors and prints them to the log (which is where you saw the error)
        logging.error(f"Install failed: {e}")
        return False