"""Start Slouchbuddy automatically at login (macOS, Windows and Linux)."""
import os
import plistlib
import subprocess
import sys

LABEL = "com.slouchbuddy.menubar"
OLD_LABELS = ("com.posturemonitor.reminder", "com.posturemonitor.menubar")  # earlier names
WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_VALUE = "Slouchbuddy"


def login_module():
    """The module run at login: the menu bar app on macOS, the buddy elsewhere."""
    return "slouchbuddy.menubar" if sys.platform == "darwin" else "slouchbuddy.buddy"


# --- macOS ---------------------------------------------------------------
def plist_path(label=LABEL):
    return os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents", f"{label}.plist")


def build_plist(python=None, camera_index=None):
    return {
        "Label": LABEL,
        "ProgramArguments": [python or sys.executable, "-m", "slouchbuddy.menubar"],
        "EnvironmentVariables": {"CAMERA_INDEX": str(camera_index or os.environ.get("CAMERA_INDEX", 0))},
        "RunAtLoad": True,
        "KeepAlive": True,
    }


def _launchctl(action, path):
    subprocess.run(["launchctl", action, path], check=False, stderr=subprocess.DEVNULL)


def _install_macos(camera_index):
    for old in OLD_LABELS:  # replace the old reminder-only login item if present
        old_path = plist_path(old)
        if os.path.exists(old_path):
            _launchctl("unload", old_path)
            os.remove(old_path)

    path = plist_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        plistlib.dump(build_plist(camera_index=camera_index), f)
    _launchctl("unload", path)
    _launchctl("load", path)
    return path


# --- Windows -------------------------------------------------------------
def windows_command(python=None):
    """Registry value: run the buddy with pythonw (no console window) when available."""
    python = python or sys.executable
    pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else python
    return f'"{exe}" -m {login_module()}'


def _install_windows(camera_index):
    import winreg

    if camera_index is not None:
        print("Note: set the CAMERA_INDEX environment variable in Windows to choose a camera.")
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, WINDOWS_VALUE, 0, winreg.REG_SZ, windows_command())
    return f"HKCU\\{WINDOWS_RUN_KEY}\\{WINDOWS_VALUE}"


# --- Linux ---------------------------------------------------------------
def desktop_entry_path():
    config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(config_home, "autostart", "slouchbuddy.desktop")


def build_desktop_entry(python=None):
    return (
        "[Desktop Entry]\nType=Application\nName=Slouchbuddy\n"
        f"Exec={python or sys.executable} -m {login_module()}\nX-GNOME-Autostart-enabled=true\n"
    )


def _install_linux(camera_index):
    path = desktop_entry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(build_desktop_entry())
    return path


# --- public API ----------------------------------------------------------
def install(camera_index=None):
    if sys.platform == "darwin":
        where = _install_macos(camera_index)
    elif sys.platform.startswith("win"):
        where = _install_windows(camera_index)
    else:
        where = _install_linux(camera_index)
    print(f"Installed. Slouchbuddy will start at login.\n({where})")


def uninstall():
    if sys.platform == "darwin":
        path = plist_path()
        _launchctl("unload", path)
        if os.path.exists(path):
            os.remove(path)
    elif sys.platform.startswith("win"):
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, WINDOWS_VALUE)
        except FileNotFoundError:
            pass
    else:
        path = desktop_entry_path()
        if os.path.exists(path):
            os.remove(path)
    print("Uninstalled.")
