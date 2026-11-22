"""Draws the koala buddy (all in code, no image assets).

`render(mood, t, size)` returns a transparent RGBA image of the koala in the given mood at
animation time `t` (seconds). The menu bar icon, the desktop buddy and the dashboard share it.
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

from slouchbuddy.buddy_brain import COFFEE, CURIOUS, HAPPY, SLEEPING, SLOUCHING, WORRIED

MOODS = (HAPPY, SLOUCHING, WORRIED, CURIOUS, SLEEPING, COFFEE)

FUR = "#b3bcc6"
FUR_LIGHT = "#c6ced7"
OUTLINE = "#3b4250"
EAR_INNER = "#f7c3d0"
MUZZLE = "#e6ebf0"
NOSE = "#343a45"
NOSE_SHINE = "#7c8591"
BLUSH = "#f6a6b8"
EYE = "#2d323d"
MOUTH_IN = "#e8798c"
SWEAT = "#9ad3ff"

BASE = 400  # all coordinates below are in a 400x400 design space
SUPERSAMPLE = 4
FRAMES_PER_MOOD = 8
FRAME_SECONDS = 0.25  # menu bar icon animation step
ART_VERSION = 3  # bump when the artwork changes so cached menu bar icons are re-rendered
HEAD_SCALE = 0.88  # head size relative to the canvas (leaves room for ears/tilt)


def _pose(mood, t):
    """(vertical offset, rotation in degrees) of the head for this mood and time."""
    if mood == HAPPY:
        return -abs(math.sin(t * 3.2)) * 14, math.sin(t * 1.6) * 2
    if mood == SLOUCHING:
        return 24 + math.sin(t * 1.5) * 3, 9
    if mood == WORRIED:
        return 12, math.sin(t * 28) * 2.5
    if mood == CURIOUS:
        return 0, math.sin(t * 1.3) * 10
    if mood == SLEEPING:
        return 14 + math.sin(t * 1.2) * 4, -6
    return math.sin(t * 2) * 4, 0  # COFFEE


def _font(px):
    try:
        return ImageFont.load_default(size=max(8, int(px)))
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def render(mood, t=0.0, size=160, outline_width=None, supersample=SUPERSAMPLE):
    """Render the koala. `outline_width` is in design units (thicker reads better when tiny)."""
    big = size >= 96
    ow = outline_width or (6 if big else 12)
    n = size * supersample
    k = n / BASE
    wf = ow / 6  # line-width boost so facial features survive at menu bar size

    def px(v):
        return v * k

    head = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(head)

    def oval(cx, cy, rx, ry, fill, outline=None, width=ow):
        d.ellipse([px(cx - rx), px(cy - ry), px(cx + rx), px(cy + ry)], fill=fill,
                  outline=outline, width=max(1, int(px(width))) if outline else 0)

    def arc(box, start, end, width=7):
        x0, y0, x1, y1 = box
        d.arc([px(x0), px(y0), px(x1), px(y1)], start, end, fill=OUTLINE, width=max(1, int(px(width * wf))))

    def line(x0, y0, x1, y1, width=6):
        d.line([px(x0), px(y0), px(x1), px(y1)], fill=OUTLINE, width=max(1, int(px(width * wf))))

    # --- ears, head, muzzle, nose -------------------------------------------------
    for ex in (86, 314):
        oval(ex, 112, 62, 62, FUR, OUTLINE)
        oval(ex, 118, 36, 36, EAR_INNER)
    oval(200, 212, 152, 124, FUR, OUTLINE)
    oval(200, 150, 70, 26, FUR_LIGHT)  # soft forehead highlight
    oval(200, 266, 76, 46, MUZZLE)
    oval(200, 240, 27, 30, NOSE)
    oval(191, 229, 8, 7, NOSE_SHINE)

    # --- cheeks: every mood gets rosy ones (the cute factor) ---------------------
    oval(94, 252, 25, 15, BLUSH)
    oval(306, 252, 25, 15, BLUSH)

    # --- eyes ----------------------------------------------------------------------
    blink = (t % 4.5) < 0.15
    ey = 204
    ex_left, ex_right = 126, 274

    def glossy_eye(x, y, r):
        oval(x, y, r, r, EYE)
        oval(x - r * 0.32, y - r * 0.38, r * 0.40, r * 0.40, "white")
        oval(x + r * 0.34, y + r * 0.36, r * 0.17, r * 0.17, "white")

    def smile_eye(x, y):  # ^ shaped, happy closed eye
        arc((x - 19, y - 12, x + 19, y + 18), 200, 340, 8)

    def sleep_eye(x, y):  # u shaped, peaceful closed eye
        arc((x - 19, y - 14, x + 19, y + 14), 20, 160, 7)

    for x in (ex_left, ex_right):
        if mood in (SLEEPING, SLOUCHING) or (blink and mood in (CURIOUS, WORRIED)):
            sleep_eye(x, ey)  # peaceful / lazy closed eyes
        elif mood in (HAPPY, COFFEE):
            smile_eye(x, ey)
        elif mood == WORRIED:  # wide-eyed "oops!"
            glossy_eye(x, ey, 22)
        else:  # CURIOUS: one eye a little bigger
            glossy_eye(x, ey, 19 if x == ex_left else 24)

    # --- mouth ---------------------------------------------------------------------
    if mood in (HAPPY, COFFEE):  # open happy smile
        d.pieslice([px(178), px(272), px(222), px(306)], 0, 180, fill=MOUTH_IN, outline=OUTLINE,
                   width=max(1, int(px(4 * wf))))
    elif mood == SLOUCHING:  # lazy little smile
        arc((180, 276, 220, 304), 20, 160, 6)
    elif mood == WORRIED:  # surprised "oh!"
        oval(200, 296, 9, 11, MOUTH_IN, OUTLINE, 4)
    elif mood == CURIOUS:
        oval(200, 294, 6, 7, MOUTH_IN, OUTLINE, 4)
    else:  # SLEEPING: tiny content smile
        arc((186, 280, 214, 302), 20, 160, 5)

    # --- shrink, then move/tilt the head (pivot near the chin so a slouch looks like drooping).
    # Shrinking first leaves margin so a tilted ear never gets clipped at the image edge.
    w = int(n * HEAD_SCALE)
    placed = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    placed.alpha_composite(head.resize((w, w), Image.LANCZOS), ((n - w) // 2, int(px(22))))
    dy, rot = _pose(mood, t)
    placed = placed.rotate(rot, resample=Image.BICUBIC, center=(n / 2, px(290)))
    img = ImageChops.offset(placed, 0, int(px(dy)))
    d = ImageDraw.Draw(img)

    if big:
        # Little paws holding the edge (fully visible, not cut off).
        for pxc in ((94,) if mood == COFFEE else (94, 306)):
            oval(pxc, 350, 44, 27, FUR, OUTLINE)
            for toe in (-14, 0, 14):  # tiny toe lines
                d.line([px(pxc + toe), px(340), px(pxc + toe), px(350)], fill=OUTLINE,
                       width=max(1, int(px(3))))

    if mood == WORRIED:
        sy = 150 + math.sin(t * 5) * 5
        d.ellipse([px(326), px(sy), px(352), px(sy + 36)], fill=SWEAT, outline=OUTLINE,
                  width=max(1, int(px(4))))
    elif mood == SLOUCHING and big:  # a lazy little "~" drifting up
        d.text((px(318), px(70 + math.sin(t * 2) * 6)), "~", fill=OUTLINE, font=_font(px(46)))
    elif mood == SLEEPING and big:
        for i in range(3):
            phase = (t * 0.7 + i * 0.33) % 1
            d.text((px(292 + i * 24), px(110 - phase * 60 - i * 16)), "z", fill=OUTLINE,
                   font=_font(px(32 + i * 8)))
    elif mood == CURIOUS and big:
        d.text((px(326), px(44)), "?", fill=OUTLINE, font=_font(px(60)))
    elif mood == COFFEE:
        d.rounded_rectangle([px(262), px(296), px(346), px(382)], radius=px(12), fill="white",
                            outline=OUTLINE, width=max(1, int(px(6))))
        d.rectangle([px(268), px(302), px(340), px(314)], fill="#8a5a3c")
        d.arc([px(330), px(314), px(376), px(358)], 270, 90, fill=OUTLINE, width=max(1, int(px(6))))
        for i, sx in enumerate((284, 312)):
            wob = math.sin(t * 4 + i) * 5
            line(sx, 288, sx + wob, 262, 5)

    return img.resize((size, size), Image.LANCZOS)


def icon_frame_paths(mood, cache_dir, size=40):
    """PNG paths for the looping menu bar animation of `mood` (rendered once, then cached)."""
    os.makedirs(cache_dir, exist_ok=True)
    paths = []
    for i in range(FRAMES_PER_MOOD):
        path = os.path.join(cache_dir, f"koala_v{ART_VERSION}_{mood}_{size}_{i}.png")
        if not os.path.exists(path):
            render(mood, t=i * FRAME_SECONDS, size=size).save(path)
        paths.append(path)
    return paths
