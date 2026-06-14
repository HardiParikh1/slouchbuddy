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

        print("Nose:", key_points["nose"])
        print("Left Shoulder:", key_points["left_shoulder"])
        print("Right Shoulder:", key_points["right_shoulder"])

    cv2.imshow("Posture Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
pose.close()
cv2.destroyAllWindows()