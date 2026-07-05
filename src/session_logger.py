import csv
import os
import time
from datetime import datetime

import config


class SessionLogger:
    def __init__(self, sessions_dir=None, interval_seconds=None):
        sessions_dir = sessions_dir or config.SESSIONS_DIR
        self.interval_seconds = interval_seconds or config.SESSION_LOG_INTERVAL_SECONDS
        self._last_log_time = 0

        resolved_dir = os.path.join(config.PROJECT_ROOT, sessions_dir)
        os.makedirs(resolved_dir, exist_ok=True)

        filename = datetime.now().strftime("session_%Y%m%d_%H%M%S.csv")
        self.path = os.path.join(resolved_dir, filename)

        self._file = open(self.path, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow(["timestamp", "posture_score", "status", "bad_duration"])

    def log(self, posture_score, status, bad_duration):
        now = time.time()
        if now - self._last_log_time < self.interval_seconds:
            return

        self._last_log_time = now
        self._writer.writerow(
            [datetime.now().isoformat(timespec="seconds"), posture_score, status, f"{bad_duration:.1f}"]
        )
        self._file.flush()

    def close(self):
        self._file.close()
