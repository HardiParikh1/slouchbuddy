import cv2
import mediapipe as mp
from pose_detection import PostureDetector


mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

posture_detector = PostureDetector()
baseline_metrics = None

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()

    if not success:
        break

    # Flip like mirror
    frame = cv2.flip(frame, 1)

    # Convert BGR to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = pose.process(rgb_frame)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        posture_detector.update_landmarks(results.pose_landmarks)
        key_points = posture_detector.get_key_points(mp_pose)
        current_metrics = posture_detector.get_current_metrics(mp_pose)
        
        shoulder_imbalance = posture_detector.get_shoulder_imbalance(mp_pose)
        if shoulder_imbalance < 0.02:
            status = "GOOD"
            color = (0, 255, 0)

        elif shoulder_imbalance < 0.05:
            status = "WARNING"
            color = (0, 255, 255)

        else:
            status = "BAD"
            color = (0, 0, 255)
            
        cv2.putText(
            frame,
            f"Shoulders: {status} ({shoulder_imbalance:.3f})",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
        )

    if baseline_metrics is None:
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
        
        
    if baseline_metrics and current_metrics:
        shoulder_diff = abs(
            current_metrics["shoulder_imbalance"] - baseline_metrics["shoulder_imbalance"]
        )

        if shoulder_diff > 0.03:
            status = "BAD SHOULDER POSTURE"
            color = (0, 0, 255)
        else:
            status = "GOOD POSTURE"
            color = (0, 255, 0)

        cv2.putText(
            frame,
            status,
            (30, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
        )
    
    cv2.imshow("Posture Monitor", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("c"):
        baseline_metrics = current_metrics
        print("Calibration saved:", baseline_metrics)

    if key == ord("q"):
        break

cap.release()
pose.close()
cv2.destroyAllWindows()