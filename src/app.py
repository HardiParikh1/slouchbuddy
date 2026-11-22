"""Posture Monitor: real-time webcam loop (one iteration per video frame)."""
import os
import time

import cv2
import mediapipe as mp

import config
import ui_overlay as ui
from alert_tracker import BadPostureTracker
from calibration import load_calibration, save_calibration
from notifications import alert_bad_posture
from pose_detection import PostureDetector
from posture_analyzer import analyze_posture
from session_logger import SessionLogger

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
LANDMARK_SPEC = mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=2)
CONNECTION_SPEC = mp_drawing.DrawingSpec(color=(160, 160, 160), thickness=1)

SHORTCUTS = [("C", "Calibrate"), ("B", "Break taken"), ("Q", "Quit")]


def open_camera():
    # Set CAMERA_INDEX=1 (etc.) to pick a different camera, e.g. to avoid an iPhone.
    return cv2.VideoCapture(int(os.environ.get("CAMERA_INDEX", 0)))


def main():
    posture_detector = PostureDetector()
    baseline_metrics = load_calibration()  # None until the user presses C
    session_logger = SessionLogger()
    tracker = BadPostureTracker()
    last_break_time = time.time()

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    cap = open_camera()

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Could not read from camera (check permissions / CAMERA_INDEX).")
                break

            frame = cv2.flip(frame, 1)  # mirror view

            # OpenCV frames are BGR; MediaPipe expects RGB.
            results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            current_metrics = None
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

            if baseline_metrics is None:
                ui.draw_calibration_prompt(frame)
            elif current_metrics is None:
                tracker.reset()
                ui.draw_status_card(frame, None, None, pose_detected=False)
            else:
                analysis = analyze_posture(current_metrics, baseline_metrics)

                reasons_text = None
                if analysis.is_bad_posture:
                    reasons_text = (
                        analysis.status.removeprefix("BAD POSTURE: ").replace(" + ", ", ").title()
                    )

                bad_duration, should_alert = tracker.update(analysis.is_bad_posture)

                ui.draw_status_card(frame, analysis.posture_score, reasons_text, pose_detected=True)

                if bad_duration >= tracker.threshold_seconds:
                    ui.draw_alert_toast(frame)
                if should_alert:
                    alert_bad_posture(analysis.status, analysis.posture_score)

                session_logger.log(analysis.posture_score, analysis.status, bad_duration)

            ui.draw_break_timer(frame, break_overdue, minutes, seconds)

            cv2.imshow("Posture Monitor", ui.compose_canvas(frame, SHORTCUTS))
            key = cv2.waitKey(1) & 0xFF

            if key == ord("c") and current_metrics:
                baseline_metrics = current_metrics
                save_calibration(baseline_metrics)
                print("Calibration saved:", baseline_metrics)
            elif key == ord("b"):
                last_break_time = time.time()
                print("Break taken, timer reset")
            elif key == ord("q"):
                break
    finally:
        cap.release()
        pose.close()
        session_logger.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
