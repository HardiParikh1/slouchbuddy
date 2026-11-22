"""Whimsical visuals for the dashboard: the koala (as an embedded image), its quips, falling leaves."""
import base64
import functools
import io

from slouchbuddy import buddy_brain as moods
from slouchbuddy import koala


@functools.lru_cache(maxsize=None)
def koala_uri(mood, size=220):
    """The koala as a PNG data URI, ready for an <img src>."""
    buf = io.BytesIO()
    koala.render(mood, t=0.4, size=size).save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def hero_message(avg_score):
    """(mood, quip) for the header koala, based on the selected sessions' average score."""
    if avg_score is None:
        return moods.SLEEPING, "No sessions yet... run Slouchbuddy, calibrate, and let's get sitting tall!"
    if avg_score >= 85:
        return moods.HAPPY, "Wow, your posture is eucalyptus-fresh! Keep it up."
    if avg_score >= 70:
        return moods.COFFEE, "Pretty chill posture! A few wobbly moments, but you're doing great."
    if avg_score >= 50:
        return moods.SLOUCHING, "Hmm, there's a bit of a slump in here. Roll those shoulders back?"
    return moods.WORRIED, "Oof. Time for a stretch, friend. I believe in you!"


LEAF_COUNT = 9


def leaves_html():
    """Slow falling leaves behind the page (pure CSS, ignored by pointer and screen readers)."""
    leaves = "".join(
        f'<span class="sb-leaf" style="--i:{i}">{"🍃" if i % 3 else "🌿"}</span>' for i in range(LEAF_COUNT)
    )
    return f'<div class="sb-leaves" aria-hidden="true">{leaves}</div>'
