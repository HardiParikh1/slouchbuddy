import cv2
import mediapipe as mp
import time

import config
from pose_detection import PostureDetector
from posture_analyzer import analyze_posture, get_shoulder_status
from calibration import save_calibration, load_calibration
from session_logger import SessionLogger
from notifications import alert_bad_posture
# Main Program, runs the loop; one iteration per video frame.

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
bad_posture_start_time = None
last_alert_time = None
last_break_time = time.time()

SHOULDER_STATUS_COLORS = {
    "GOOD": (0, 255, 0),
    "WARNING": (0, 255, 255),
    "BAD": (0, 0, 255),
}

posture_detector = PostureDetector()
baseline_metrics = load_calibration()  # Loaded from calibration.json if it exists
session_logger = SessionLogger()


pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

cap = cv2.VideoCapture(0)

while True:
    current_metrics = None
    success, frame = cap.read()  #reading the latest frame

    if not success:
        break

    # Flip the camera frame like mirror
    frame = cv2.flip(frame, 1)

    # Convert BGR to RGB for MediaPipe; OpenCV reads frames in BGR order & MediaPipe expects in RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = pose.process(rgb_frame) # can be None or 33 point object

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        posture_detector.update_landmarks(results.pose_landmarks)
        current_metrics = posture_detector.get_current_metrics(mp_pose)

        shoulder_status = get_shoulder_status(current_metrics["shoulder_imbalance"])
        color = SHOULDER_STATUS_COLORS[shoulder_status]

        cv2.putText(
            frame,
            f"Shoulders: {shoulder_status} ({current_metrics['shoulder_imbalance']:.3f})",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
        )

    if baseline_metrics is None: #Calibarate
        cv2.putText(
            frame,
            "Press C to calibrate good posture",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
    else:
        cv2.putText(
            frame,
            "Calibrated",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )


    time_since_break = time.time() - last_break_time
    minutes, seconds = divmod(int(time_since_break), 60)

    if time_since_break >= config.BREAK_REMINDER_SECONDS:
        cv2.putText(
            frame,
            "TAKE A BREAK! Press B once you have.",
            (30, 330),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
        )
    else:
        cv2.putText(
            frame,
            f"Time since last break: {minutes:02d}:{seconds:02d}",
            (30, 330),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

    if baseline_metrics and current_metrics:
        analysis = analyze_posture(current_metrics, baseline_metrics)
        posture_status = analysis.status
        is_bad_posture = analysis.is_bad_posture
        head_forward_diff = analysis.head_forward_diff
        posture_score = analysis.posture_score
        posture_color = (0, 0, 255) if is_bad_posture else (0, 255, 0)

        if posture_score >= 80:
            score_color = (0, 255, 0)
        elif posture_score >= 50:
            score_color = (0, 255, 255)
        else:
            score_color = (0, 0, 255)

        if is_bad_posture:
            if bad_posture_start_time is None:
                bad_posture_start_time = time.time()

            bad_duration = time.time() - bad_posture_start_time

        else:
            bad_posture_start_time = None
            bad_duration = 0

        cv2.putText(
            frame,
            posture_status,
            (30, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            posture_color,
            2,
        )
        cv2.putText(
            frame,
            f"Head diff: {head_forward_diff:.3f}",
            (30, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Bad posture time: {bad_duration:.1f}s",
            (30, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Posture Score: {posture_score}/100",
            (30, 250),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            score_color,
            2,
        )

        if bad_duration >= config.BAD_POSTURE_THRESHOLD_SECONDS:
            cv2.putText(
                frame,
                "ALERT: Fix your posture!",
                (30, 290),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                3,
            )

            if (
                last_alert_time is None
                or time.time() - last_alert_time >= config.ALERT_COOLDOWN_SECONDS
            ):
                alert_bad_posture(posture_status, posture_score)
                last_alert_time = time.time()

        session_logger.log(posture_score, posture_status, bad_duration)


    cv2.imshow("Posture Monitor", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("c") and current_metrics:
        baseline_metrics = current_metrics
        save_calibration(baseline_metrics)
        print("Calibration saved:", baseline_metrics)

    if key == ord("b"):
        last_break_time = time.time()
        print("Break taken, timer reset")

    if key == ord("q"):
        break

cap.release()
pose.close()
session_logger.close()
cv2.destroyAllWindows()