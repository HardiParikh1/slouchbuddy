class PostureDetector:
    def __init__(self):
        self.landmarks = None

    def update_landmarks(self, pose_landmarks):
        self.landmarks = pose_landmarks

    def get_landmark(self, landmark_id):
        if not self.landmarks:
            return None
        return self.landmarks.landmark[landmark_id]
    
    def get_midpoint(self, point1, point2):
        if not point1 or not point2:
            return None

        return {
            "x": (point1.x + point2.x) / 2,
            "y": (point1.y + point2.y) / 2,
            "z": (point1.z + point2.z) / 2,
        }


    def get_current_metrics(self, mp_pose):
        key_points = self.get_key_points(mp_pose)

        if not key_points:
            return None

        left_shoulder = key_points["left_shoulder"]
        right_shoulder = key_points["right_shoulder"]
        nose = key_points["nose"]
        mouth_left = key_points["mouth_left"]
        mouth_right = key_points["mouth_right"]

        shoulder_midpoint = self.get_midpoint(left_shoulder, right_shoulder)

        shoulder_imbalance = abs(left_shoulder.y - right_shoulder.y)
        shoulder_width = abs(left_shoulder.x - right_shoulder.x)
        mouth_width = abs(mouth_left.x - mouth_right.x)

        nose_to_shoulder_y = abs(nose.y - shoulder_midpoint["y"])
        nose_to_shoulder_x = abs(nose.x - shoulder_midpoint["x"])

        return {
            "shoulder_imbalance": shoulder_imbalance,
            "shoulder_width": shoulder_width,
            "mouth_width": mouth_width,
            "nose_to_shoulder_y": nose_to_shoulder_y,
            "nose_to_shoulder_x": nose_to_shoulder_x,
            "shoulder_mid_y": shoulder_midpoint["y"],
        }
    
    def get_shoulder_imbalance(self, mp_pose):
        key_points = self.get_key_points(mp_pose)

        if not key_points:
            return None

        left_shoulder = key_points["left_shoulder"]
        right_shoulder = key_points["right_shoulder"]

        imbalance = abs(left_shoulder.y - right_shoulder.y)

        return imbalance

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