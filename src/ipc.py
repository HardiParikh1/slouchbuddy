"""File-based IPC between the menu bar app and the background monitor process.

The monitor writes a small status file once a second; the menu bar app reads it and
drops one-line commands into a control file that the monitor polls.
"""
import json
import os
import time

import config

COMMANDS = {"show", "hide", "toggle", "calibrate", "break", "pause", "resume", "quit"}


def _dir(base_dir=None):
    path = base_dir or os.path.join(config.PROJECT_ROOT, "data")
    os.makedirs(path, exist_ok=True)
    return path


def write_status(status, base_dir=None):
    path = os.path.join(_dir(base_dir), "status.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({**status, "updated": time.time()}, f)
    os.replace(tmp, path)  # atomic: readers never see a half-written file


def read_status(base_dir=None, max_age=5.0):
    """Latest status, or None if missing, unreadable or stale (monitor not running)."""
    path = os.path.join(_dir(base_dir), "status.json")
    try:
        with open(path) as f:
            status = json.load(f)
    except (OSError, ValueError):
        return None
    if time.time() - status.get("updated", 0) > max_age:
        return None
    return status


def send_command(name, base_dir=None):
    if name not in COMMANDS:
        raise ValueError(f"unknown command: {name}")
    with open(os.path.join(_dir(base_dir), "control.txt"), "a") as f:
        f.write(name + "\n")


def pop_commands(base_dir=None):
    """Return and clear all pending commands, in order."""
    control = os.path.join(_dir(base_dir), "control.txt")
    claimed = control + ".reading"
    try:
        os.replace(control, claimed)  # claim atomically so no command is lost or run twice
    except FileNotFoundError:
        return []
    with open(claimed) as f:
        commands = [line.strip() for line in f if line.strip() in COMMANDS]
    os.remove(claimed)
    return commands
