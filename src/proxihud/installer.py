import os
import sys
import shutil
import logging
import re
from . import config

def get_source_addon_path():
    """Finds the bundled source files."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        return os.path.join(base_path, "src", "proxihud", "resources", "addon", "ProxiHUD_Bridge")
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "resources", "addon", "ProxiHUD_Bridge"))

def get_addon_version(manifest_path):
    """Parses the '## Version: X.Y' line from a manifest file."""
    if not os.path.exists(manifest_path):
        return 0.0

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"## Version:\s*([\d\.]+)", content)
            if match:
                return float(match.group(1))
    except: pass
    return 0.0

def is_installed():
    """
    Checks if installed AND up-to-date.
    Returns False if missing OR if old version.
    """
    try:
        eso_path = config.get_eso_addon_path()
        if not eso_path: return False

        installed_manifest = os.path.join(eso_path, "ProxiHUD_Bridge", "ProxiHUD_Bridge.txt")
        source_manifest = os.path.join(get_source_addon_path(), "ProxiHUD_Bridge.txt")

        # 1. Check existence
        if not os.path.exists(installed_manifest):
            return False

        # 2. Check Version
        installed_ver = get_addon_version(installed_manifest)
        source_ver = get_addon_version(source_manifest)

        if source_ver > installed_ver:
            logging.info(f"Addon Update Available: v{installed_ver} -> v{source_ver}")
            return False # Return False to trigger the 'Install' flow in the Wizard

        return True
    except:
        return False

def install_addon():
    """Copies files (Force Overwrite)."""
    try:
        source_dir = get_source_addon_path()
        eso_addons_path = config.get_eso_addon_path()
        dest_dir = os.path.join(eso_addons_path, "ProxiHUD_Bridge")

        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)

        shutil.copytree(source_dir, dest_dir)
        logging.info(f"Addon installed/updated to: {dest_dir}")
        return True
    except Exception as e:
        logging.error(f"Install failed: {e}")
        return False