import json
import os

import config
from config import CALIBRATION_FILE


def _resolve_path(path):
    if os.path.isabs(path):
        return path
    return os.path.join(config.PROJECT_ROOT, path)


def save_calibration(metrics, path=CALIBRATION_FILE):
    resolved = _resolve_path(path)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w") as f:
        json.dump(metrics, f, indent=2)


def load_calibration(path=CALIBRATION_FILE):
    resolved = _resolve_path(path)
    if not os.path.exists(resolved):
        return None

    with open(resolved) as f:
        return json.load(f)
