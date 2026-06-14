class PostureDetector:
    def __init__(self):
        self.landmarks = None

    def update_landmarks(self, pose_landmarks):
        self.landmarks = pose_landmarks

    def get_landmark(self, landmark_id):
        if not self.landmarks:
            return None
        return self.landmarks.landmark[landmark_id]

    def get_key_points(self, mp_pose):
        if not self.landmarks:
            return None

        return {
            # Required for desk posture
            "nose": self.get_landmark(mp_pose.PoseLandmark.NOSE),
            "left_ear": self.get_landmark(mp_pose.PoseLandmark.LEFT_EAR),
            "right_ear": self.get_landmark(mp_pose.PoseLandmark.RIGHT_EAR),
            "left_shoulder": self.get_landmark(mp_pose.PoseLandmark.LEFT_SHOULDER),
            "right_shoulder": self.get_landmark(mp_pose.PoseLandmark.RIGHT_SHOULDER),
            "mouth_left": self.get_landmark(mp_pose.PoseLandmark.MOUTH_LEFT),
            "mouth_right": self.get_landmark(mp_pose.PoseLandmark.MOUTH_RIGHT),

            # Optional for slouch/spine if visible
            "left_hip": self.get_landmark(mp_pose.PoseLandmark.LEFT_HIP),
            "right_hip": self.get_landmark(mp_pose.PoseLandmark.RIGHT_HIP),
        }