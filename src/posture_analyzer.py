from dataclasses import dataclass

import config


@dataclass
class PostureAnalysis:
    status: str
    posture_score: int
    is_bad_posture: bool

    shoulder_diff: float
    head_forward_diff: float
    head_tilt_diff: float
    screen_proximity_diff: float


def get_shoulder_status(shoulder_imbalance):
    if shoulder_imbalance < config.SHOULDER_GOOD_THRESHOLD:
        return "GOOD"
    elif shoulder_imbalance < config.SHOULDER_WARNING_THRESHOLD:
        return "WARNING"
    else:
        return "BAD"


def _factor_penalty(diff, threshold, weight):
    ratio = diff / threshold

    if ratio <= 1:
        return 0

    severity = min(ratio, config.POSTURE_SCORE_SEVERITY_CAP)
    fraction = (severity - 1) / (config.POSTURE_SCORE_SEVERITY_CAP - 1)
    return weight * fraction


def calculate_posture_score(
    shoulder_diff, head_forward_diff, head_tilt_diff, screen_proximity_diff
):
    penalty = 0
    penalty += _factor_penalty(
        shoulder_diff,
        config.SHOULDER_IMBALANCE_DIFF_THRESHOLD,
        config.POSTURE_SCORE_WEIGHTS["shoulder"],
    )
    penalty += _factor_penalty(
        head_forward_diff,
        config.HEAD_FORWARD_DIFF_THRESHOLD,
        config.POSTURE_SCORE_WEIGHTS["head_forward"],
    )
    penalty += _factor_penalty(
        head_tilt_diff,
        config.HEAD_TILT_DIFF_THRESHOLD,
        config.POSTURE_SCORE_WEIGHTS["head_tilt"],
    )
    penalty += _factor_penalty(
        max(screen_proximity_diff, 0),
        config.SCREEN_PROXIMITY_DIFF_THRESHOLD,
        config.POSTURE_SCORE_WEIGHTS["screen_distance"],
    )

    return round(max(0, 100 - penalty))


def analyze_posture(current_metrics, baseline_metrics):
    shoulder_diff = abs(
        current_metrics["shoulder_imbalance"] - baseline_metrics["shoulder_imbalance"]
    )
    head_forward_diff = abs(
        current_metrics["nose_to_shoulder_x"] - baseline_metrics["nose_to_shoulder_x"]
    )
    head_tilt_diff = abs(
        current_metrics["head_tilt_angle"] - baseline_metrics["head_tilt_angle"]
    )
    screen_proximity_diff = (
        current_metrics["mouth_width"] - baseline_metrics["mouth_width"]
    )

    bad_shoulder = shoulder_diff > config.SHOULDER_IMBALANCE_DIFF_THRESHOLD
    bad_head = head_forward_diff > config.HEAD_FORWARD_DIFF_THRESHOLD
    bad_tilt = head_tilt_diff > config.HEAD_TILT_DIFF_THRESHOLD
    bad_screen_distance = screen_proximity_diff > config.SCREEN_PROXIMITY_DIFF_THRESHOLD

    head_too_low = (
        current_metrics["head_above_shoulders"] < config.HEAD_LEVEL_MIN_GAP
    )

    bad_reasons = []

    if bad_shoulder:
        bad_reasons.append("SHOULDERS")

    if bad_head:
        bad_reasons.append("HEAD FORWARD")

    if bad_tilt:
        bad_reasons.append("HEAD TILT")

    if bad_screen_distance:
        bad_reasons.append("SCREEN DISTANCE")

    if head_too_low:
        bad_reasons.append("HEAD LEVEL WITH SHOULDERS")

    if bad_reasons:
        status = "BAD POSTURE: " + " + ".join(bad_reasons)
    else:
        status = "GOOD POSTURE"

    posture_score = calculate_posture_score(
        shoulder_diff, head_forward_diff, head_tilt_diff, screen_proximity_diff
    )

    if head_too_low:
        posture_score = min(posture_score, config.HEAD_LEVEL_SCORE_CAP)

    return PostureAnalysis(
        status=status,
        posture_score=posture_score,
        is_bad_posture=bool(bad_reasons),
        shoulder_diff=shoulder_diff,
        head_forward_diff=head_forward_diff,
        head_tilt_diff=head_tilt_diff,
        screen_proximity_diff=screen_proximity_diff,
    )
