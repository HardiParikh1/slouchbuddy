"""Posture Monitor: real-time webcam loop (one iteration per video frame).

    python src/app.py                 # foreground: live window, Q quits
    python src/app.py --background    # runs hidden, controlled by the menu bar app (see menubar.py)
"""
import argparse
import os
import time

import cv2
import mediapipe as mp

import config
import ipc
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
WINDOW_NAME = "Posture Monitor"
CAMERA_RETRY_SECONDS = 3
HIDDEN_FRAME_DELAY = 0.05  # ~15 fps is plenty when nobody is looking at the window


def open_camera():
    # Set CAMERA_INDEX=1 (etc.) to pick a different camera, e.g. to avoid an iPhone.
    return cv2.VideoCapture(int(os.environ.get("CAMERA_INDEX", 0)))


def main(background=False):
    posture_detector = PostureDetector()
    baseline_metrics = load_calibration()  # None until the user calibrates
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

    cap = None
    window_visible = not background
    paused = False
    calibrate_requested = False
    last_status_write = 0

    def publish(state, score=None, reasons=None, force=False):
        nonlocal last_status_write
        now = time.time()
        if background and (force or now - last_status_write >= 1):
            last_status_write = now
            ipc.write_status(
                {
                    "state": state,
                    "score": score,
                    "reasons": reasons,
                    "calibrated": baseline_metrics is not None,
                    "window_visible": window_visible,
                    "break_overdue": now - last_break_time >= config.BREAK_REMINDER_SECONDS,
                }
            )

    def hide_window():
        nonlocal window_visible
        window_visible = False
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # let macOS actually close it

    try:
        while True:
            quit_requested = False
            if background:
                for command in ipc.pop_commands():
                    if command == "quit":
                        quit_requested = True
                    elif command == "show":
                        window_visible = True
                    elif command == "hide":
                        hide_window()
                    elif command == "toggle":
                        if window_visible:
                            hide_window()
                        else:
                            window_visible = True
                    elif command == "calibrate":
                        calibrate_requested = True
                    elif command == "break":
                        last_break_time = time.time()
                    elif command == "pause":
                        paused = True
                    elif command == "resume":
                        paused = False
            if quit_requested:
                break

            if paused:
                # Release the camera entirely so the green light goes off.
                if cap is not None:
                    cap.release()
                    cap = None
                tracker.reset()
                if window_visible:
                    hide_window()
                publish("paused", force=True)
                time.sleep(0.3)
                continue

            if cap is None:
                cap = open_camera()

            success, frame = cap.read()
            if not success:
                if not background:
                    print("Could not read from camera (check permissions / CAMERA_INDEX).")
                    break
                cap.release()
                cap = None
                publish("camera_error", force=True)
                time.sleep(CAMERA_RETRY_SECONDS)
                continue

            frame = cv2.flip(frame, 1)  # mirror view

            # OpenCV frames are BGR; MediaPipe expects RGB.
            results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            current_metrics = None
            if results.pose_landmarks:
                posture_detector.update_landmarks(results.pose_landmarks)
                current_metrics = posture_detector.get_current_metrics(mp_pose)
                if window_visible:
                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=LANDMARK_SPEC,
                        connection_drawing_spec=CONNECTION_SPEC,
                    )

            if calibrate_requested and current_metrics:
                baseline_metrics = current_metrics
                save_calibration(baseline_metrics)
                calibrate_requested = False
                print("Calibration saved")

            time_since_break = time.time() - last_break_time
            minutes, seconds = divmod(int(time_since_break), 60)
            break_overdue = time_since_break >= config.BREAK_REMINDER_SECONDS

            if baseline_metrics is None:
                publish("uncalibrated")
                if window_visible:
                    ui.draw_calibration_prompt(frame)
            elif current_metrics is None:
                tracker.reset()
                publish("no_pose")
                if window_visible:
                    ui.draw_status_card(frame, None, None, pose_detected=False)
            else:
                analysis = analyze_posture(current_metrics, baseline_metrics)

                reasons_text = None
                if analysis.is_bad_posture:
                    reasons_text = (
                        analysis.status.removeprefix("BAD POSTURE: ").replace(" + ", ", ").title()
                    )

                bad_duration, should_alert = tracker.update(analysis.is_bad_posture)
                publish("bad" if analysis.is_bad_posture else "good", analysis.posture_score, reasons_text)

                if window_visible:
                    ui.draw_status_card(frame, analysis.posture_score, reasons_text, pose_detected=True)
                    if bad_duration >= tracker.threshold_seconds:
                        ui.draw_alert_toast(frame)
                if should_alert:
                    alert_bad_posture(analysis.status, analysis.posture_score)

                session_logger.log(analysis.posture_score, analysis.status, bad_duration)

            if not window_visible:
                time.sleep(HIDDEN_FRAME_DELAY)
                continue

            ui.draw_break_timer(frame, break_overdue, minutes, seconds)
            cv2.imshow(WINDOW_NAME, ui.compose_canvas(frame, SHORTCUTS))
            key = cv2.waitKey(1) & 0xFF

            closed = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1
            if key == ord("c") and current_metrics:
                baseline_metrics = current_metrics
                save_calibration(baseline_metrics)
                print("Calibration saved:", baseline_metrics)
            elif key == ord("b"):
                last_break_time = time.time()
                print("Break taken, timer reset")
            elif key == ord("q") or closed:
                if background:
                    hide_window()  # keep monitoring; the menu bar can bring the window back
                else:
                    break
    finally:
        if cap is not None:
            cap.release()
        pose.close()
        session_logger.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Posture Monitor")
    parser.add_argument("--background", action="store_true", help="run hidden, controlled via the menu bar app")
    main(background=parser.parse_args().background)
