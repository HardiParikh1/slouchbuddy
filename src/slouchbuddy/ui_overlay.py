import cv2
import numpy as np

FONT = cv2.FONT_HERSHEY_SIMPLEX

# Colors are BGR (OpenCV convention), pulled from the project's dark palette.
COLOR_CHROME_BG = (18, 18, 18)
COLOR_CARD_BG = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_MUTED = (150, 150, 150)
COLOR_SECONDARY = (205, 205, 205)

STATUS_COLORS = {
    "good": (12, 163, 12),
    "warning": (25, 178, 250),
    "critical": (59, 59, 208),
}
STATUS_LABELS = {"good": "Good", "warning": "Fair", "critical": "Poor"}

MARGIN = 20
BOTTOM_BAR_HEIGHT = 64
FRAME_RADIUS = 20
CARD_X, CARD_Y = 24, 24
CARD_WIDTH = 280


def score_status(score):
    if score >= 80:
        return "good"
    elif score >= 50:
        return "warning"
    else:
        return "critical"


def _rounded_rect_mask(h, w, radius):
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(mask, (radius, 0), (w - radius, h), 255, -1)
    cv2.rectangle(mask, (0, radius), (w, h - radius), 255, -1)
    for cx, cy in [(radius, radius), (w - radius, radius), (radius, h - radius), (w - radius, h - radius)]:
        cv2.circle(mask, (cx, cy), radius, 255, -1)
    return mask


def round_frame_corners(frame, radius, bg_color):
    h, w = frame.shape[:2]
    mask = _rounded_rect_mask(h, w, radius)
    bg = np.full_like(frame, bg_color, dtype=np.uint8)
    mask_3ch = cv2.merge([mask, mask, mask])
    return np.where(mask_3ch == 255, frame, bg)


def draw_translucent_rounded_rect(img, top_left, bottom_right, radius, color, alpha):
    x1, y1 = top_left
    x2, y2 = bottom_right
    radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    overlay = img.copy()
    cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    for cx, cy in [(x1 + radius, y1 + radius), (x2 - radius, y1 + radius),
                   (x1 + radius, y2 - radius), (x2 - radius, y2 - radius)]:
        cv2.circle(overlay, (cx, cy), radius, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, dst=img)


def _put_text(img, text, org, scale, color, thickness=1):
    cv2.putText(img, text, org, FONT, scale, color, thickness, cv2.LINE_AA)


def draw_calibration_prompt(frame):
    text = "Press C to calibrate"
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.55, 1)
    width, height = tw + 40, 46
    draw_translucent_rounded_rect(frame, (CARD_X, CARD_Y), (CARD_X + width, CARD_Y + height), 16, COLOR_CARD_BG, 0.55)
    _put_text(frame, text, (CARD_X + 20, CARD_Y + 30), 0.55, COLOR_WHITE, 1)


def draw_status_card(frame, score, reasons_text, pose_detected):
    if not pose_detected:
        text = "No pose detected"
        (tw, th), _ = cv2.getTextSize(text, FONT, 0.5, 1)
        width, height = tw + 40, 44
        draw_translucent_rounded_rect(frame, (CARD_X, CARD_Y), (CARD_X + width, CARD_Y + height), 16, COLOR_CARD_BG, 0.5)
        _put_text(frame, text, (CARD_X + 20, CARD_Y + 28), 0.5, COLOR_MUTED, 1)
        return

    status_key = score_status(score)
    color = STATUS_COLORS[status_key]
    height = 150 if reasons_text else 118

    draw_translucent_rounded_rect(
        frame, (CARD_X, CARD_Y), (CARD_X + CARD_WIDTH, CARD_Y + height), 18, COLOR_CARD_BG, 0.55
    )

    _put_text(frame, "POSTURE SCORE", (CARD_X + 20, CARD_Y + 30), 0.42, COLOR_MUTED, 1)
    _put_text(frame, f"{score}", (CARD_X + 20, CARD_Y + 76), 1.1, COLOR_WHITE, 2)
    (sw, _), _ = cv2.getTextSize(f"{score}", FONT, 1.1, 2)
    _put_text(frame, "/100", (CARD_X + 26 + sw, CARD_Y + 76), 0.5, COLOR_MUTED, 1)

    cv2.circle(frame, (CARD_X + 20, CARD_Y + 100), 5, color, -1)
    _put_text(frame, STATUS_LABELS[status_key], (CARD_X + 34, CARD_Y + 105), 0.5, color, 1)

    if reasons_text:
        _put_text(frame, reasons_text, (CARD_X + 20, CARD_Y + 134), 0.42, COLOR_MUTED, 1)


def draw_break_timer(frame, overdue, minutes, seconds):
    h, w = frame.shape[:2]
    text = "TAKE A BREAK" if overdue else f"{minutes:02d}:{seconds:02d}"
    color = STATUS_COLORS["critical"] if overdue else COLOR_SECONDARY
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.5, 1)
    width, height = tw + 44, 42
    x = w - width - 24
    y = 24
    draw_translucent_rounded_rect(frame, (x, y), (x + width, y + height), 16, COLOR_CARD_BG, 0.55)
    _put_text(frame, text, (x + 22, y + 27), 0.5, color, 1)


def draw_alert_toast(frame):
    h, w = frame.shape[:2]
    text = "Fix your posture"
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.55, 2)
    width, height = tw + 50, 44
    x = (w - width) // 2
    y = h - height - 24
    draw_translucent_rounded_rect(frame, (x, y), (x + width, y + height), 20, STATUS_COLORS["critical"], 0.88)
    _put_text(frame, text, (x + 25, y + 29), 0.55, COLOR_WHITE, 2)


def draw_bottom_bar(canvas, shortcuts, bar_top):
    pill_height = 36
    y = bar_top
    gap = 12
    pill_texts = [f"{key}   {label}" for key, label in shortcuts]
    widths = []
    for text in pill_texts:
        (tw, th), _ = cv2.getTextSize(text, FONT, 0.46, 1)
        widths.append(tw + 34)

    total_width = sum(widths) + gap * (len(widths) - 1)
    cx = (canvas.shape[1] - total_width) // 2

    for text, width in zip(pill_texts, widths):
        draw_translucent_rounded_rect(canvas, (cx, y), (cx + width, y + pill_height), 18, (35, 35, 35), 0.9)
        _put_text(canvas, text, (cx + 17, y + 24), 0.46, COLOR_SECONDARY, 1)
        cx += width + gap


def compose_canvas(frame, shortcuts):
    h, w = frame.shape[:2]
    canvas_h = h + MARGIN * 2 + BOTTOM_BAR_HEIGHT
    canvas_w = w + MARGIN * 2
    canvas = np.full((canvas_h, canvas_w, 3), COLOR_CHROME_BG, dtype=np.uint8)

    rounded = round_frame_corners(frame, FRAME_RADIUS, COLOR_CHROME_BG)
    canvas[MARGIN:MARGIN + h, MARGIN:MARGIN + w] = rounded

    bar_top = MARGIN + h + (BOTTOM_BAR_HEIGHT - 36) // 2
    draw_bottom_bar(canvas, shortcuts, bar_top)

    return canvas
