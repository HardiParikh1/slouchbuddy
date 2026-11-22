"""The buddy's personality: turns monitor status into a mood and the occasional comment.

Pure logic with an injectable clock (no GUI), so it is unit-tested without a display.
"""
import time
from dataclasses import dataclass
from typing import Optional

# Moods the character can draw.
HAPPY, SLOUCHING, WORRIED, CURIOUS, SLEEPING, COFFEE = (
    "happy", "slouching", "worried", "curious", "sleeping", "coffee",
)

# One hint per detected issue (checked in this order), matched against the reasons text.
ISSUE_HINTS = [
    ("level with shoulders", "Whoa, head up! Your head is down at shoulder level."),
    ("shoulders", "Shoulders are uneven. Level them out."),
    ("head forward", "Chin back, you're craning toward the screen."),
    ("screen distance", "A bit close to the screen. Lean back."),
    ("head tilt", "Your head is tilting. Straighten up."),
]
GENERIC_SLOUCH = "Posture check! Sit up tall."

MIN_BAD_SECONDS_BEFORE_COMMENT = 5
MIN_BAD_SECONDS_FOR_PRAISE = 10
SECONDS_BETWEEN_COMMENTS = 20
SLOUCH_REPEAT_SECONDS = 120  # re-nag at most this often while the slouch continues
GOOD_STREAK_MILESTONES_MIN = (15, 30, 60, 120)


@dataclass
class BuddyView:
    mood: str
    message: Optional[str] = None  # a new comment to show now, else None
    alert: bool = False  # True when the comment is a real nudge (slouch, break): play the chime too


class BuddyBrain:
    def __init__(self, clock=time.time):
        self._clock = clock
        self._bad_since = None
        self._good_since = None
        self._last_comment = -1e9
        self._last_slouch_comment = -1e9
        self._milestones_said = set()
        self._break_said = False
        self._camera_said = False
        self._uncalibrated_said = False

    def _say(self, text, now, force=False):
        if not force and now - self._last_comment < SECONDS_BETWEEN_COMMENTS:
            return None
        self._last_comment = now
        return text

    def update(self, status):
        now = self._clock()

        if status is None:
            return BuddyView(SLEEPING)

        state = status.get("state")
        overdue = bool(status.get("break_overdue"))

        if state == "paused":
            self._reset_streaks()
            return BuddyView(SLEEPING)

        if state == "camera_error":
            self._reset_streaks()
            msg = None
            if not self._camera_said:
                self._camera_said = True
                msg = self._say("I can't see you. Check the camera permission?", now, force=True)
            return BuddyView(WORRIED, msg)
        self._camera_said = False

        if state == "uncalibrated":
            msg = None
            if not self._uncalibrated_said:
                self._uncalibrated_said = True
                msg = self._say("Sit up nice and tall, then choose Calibrate from my menu.", now, force=True)
            return BuddyView(CURIOUS, msg)

        if state == "no_pose":
            self._reset_streaks()
            return BuddyView(COFFEE if overdue else CURIOUS)

        if overdue and not self._break_said:
            self._break_said = True
            msg = self._say("Time for a break! Stand up and stretch.", now, force=True)
            return BuddyView(COFFEE, msg, alert=bool(msg))
        if not overdue:
            self._break_said = False

        if state == "bad":
            self._good_since = None
            self._milestones_said.clear()
            if self._bad_since is None:
                self._bad_since = now
            bad_for = now - self._bad_since

            msg = None
            if (
                bad_for >= MIN_BAD_SECONDS_BEFORE_COMMENT
                and now - self._last_slouch_comment >= SLOUCH_REPEAT_SECONDS
            ):
                msg = self._say(self._slouch_message(status.get("reasons")), now)
                if msg:
                    self._last_slouch_comment = now
            return BuddyView(WORRIED if bad_for >= 30 else SLOUCHING, msg, alert=bool(msg))

        # state == "good"
        msg = None
        if self._bad_since is not None:
            if now - self._bad_since >= MIN_BAD_SECONDS_FOR_PRAISE:
                msg = self._say("Nice, much better!", now, force=True)
            self._bad_since = None
        if self._good_since is None:
            self._good_since = now
        good_minutes = (now - self._good_since) / 60
        for milestone in GOOD_STREAK_MILESTONES_MIN:
            if good_minutes >= milestone and milestone not in self._milestones_said:
                self._milestones_said.add(milestone)
                msg = self._say(f"{milestone} minutes of great posture. Keep it up!", now) or msg
        return BuddyView(COFFEE if overdue else HAPPY, msg)

    def _reset_streaks(self):
        self._bad_since = None
        self._good_since = None
        self._milestones_said.clear()

    @staticmethod
    def _slouch_message(reasons):
        text = (reasons or "").lower()
        for key, hint in ISSUE_HINTS:
            if key in text:
                return hint
        return GENERIC_SLOUCH
