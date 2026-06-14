import cv2
import mediapipe as mp
from pose_detection import PostureDetector


mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

posture_detector = PostureDetector()

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

    cv2.imshow("Posture Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
pose.close()
cv2.destroyAllWindows()