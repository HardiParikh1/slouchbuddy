import cv2
import mediapipe as mp
import time

import config
import ui_overlay as ui
from pose_detection import PostureDetector
from posture_analyzer import analyze_posture
from calibration import save_calibration, load_calibration
from session_logger import SessionLogger
from notifications import alert_bad_posture
# Main Program, runs the loop; one iteration per video frame.

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
LANDMARK_SPEC = mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=2)
CONNECTION_SPEC = mp_drawing.DrawingSpec(color=(160, 160, 160), thickness=1)

SHORTCUTS = [("C", "Calibrate"), ("B", "Break taken"), ("Q", "Quit")]

bad_posture_start_time = None
last_alert_time = None
last_break_time = time.time()

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
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=LANDMARK_SPEC,
            connection_drawing_spec=CONNECTION_SPEC,
        )

        posture_detector.update_landmarks(results.pose_landmarks)
        current_metrics = posture_detector.get_current_metrics(mp_pose)

    time_since_break = time.time() - last_break_time
    minutes, seconds = divmod(int(time_since_break), 60)
    break_overdue = time_since_break >= config.BREAK_REMINDER_SECONDS

    bad_duration = 0

    if baseline_metrics is None:
        ui.draw_calibration_prompt(frame)
    elif current_metrics is None:
        ui.draw_status_card(frame, None, None, pose_detected=False)
    else:
        analysis = analyze_posture(current_metrics, baseline_metrics)
        posture_score = analysis.posture_score
        is_bad_posture = analysis.is_bad_posture

        reasons_text = None
        if is_bad_posture:
            if bad_posture_start_time is None:
                bad_posture_start_time = time.time()
            bad_duration = time.time() - bad_posture_start_time
            reasons_text = analysis.status.removeprefix("BAD POSTURE: ").replace(" + ", ", ").title()
        else:
            bad_posture_start_time = None
            bad_duration = 0

        ui.draw_status_card(frame, posture_score, reasons_text, pose_detected=True)

        if bad_duration >= config.BAD_POSTURE_THRESHOLD_SECONDS:
            ui.draw_alert_toast(frame)

            if (
                last_alert_time is None
                or time.time() - last_alert_time >= config.ALERT_COOLDOWN_SECONDS
            ):
                alert_bad_posture(analysis.status, posture_score)
                last_alert_time = time.time()

        session_logger.log(posture_score, analysis.status, bad_duration)

    ui.draw_break_timer(frame, break_overdue, minutes, seconds)

    canvas = ui.compose_canvas(frame, SHORTCUTS)
    cv2.imshow("Posture Monitor", canvas)
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
