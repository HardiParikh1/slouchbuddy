import math
class PostureDetector:
    def __init__(self):
        self.landmarks = None #landmarks are points that we are saving based on mediapipes body detection; initially it is none

    def update_landmarks(self, pose_landmarks):
        self.landmarks = pose_landmarks #Based on mediapipes detection, we save the latest coordinates recorded

    def get_landmark(self, landmark_id): #landmark id is a number like 0 (nose) or 11(left shoulder). We get each point in x,y,z coordinates all normalised between 0 & 1
        if not self.landmarks:
            return None
        return self.landmarks.landmark[landmark_id]
    
    def get_midpoint(self, point1, point2): #Average of 2 points, used to find the center point between shoulders for eg. # Returns a dictonary, so accessing is done like: "x"
        if not point1 or not point2:
            return None

        return {
            "x": (point1.x + point2.x) / 2,
            "y": (point1.y + point2.y) / 2,
            "z": (point1.z + point2.z) / 2,
        }


# The main measurement method: 
# we compute all differences between different parts like nose & shoulder, shoulders etc.
# this dictonary gets saved at calibaration as baseline & compared in every frame to detect the drift.

    def get_current_metrics(self, mp_pose): 
        key_points = self.get_key_points(mp_pose)

        if not key_points:
            return None

        left_shoulder = key_points["left_shoulder"]
        right_shoulder = key_points["right_shoulder"]
        nose = key_points["nose"]
        mouth_left = key_points["mouth_left"]
        mouth_right = key_points["mouth_right"]
        left_ear  = key_points["left_ear"]
        right_ear = key_points["right_ear"]

        shoulder_midpoint = self.get_midpoint(left_shoulder, right_shoulder)

        shoulder_imbalance = abs(left_shoulder.y - right_shoulder.y)
        shoulder_width = abs(left_shoulder.x - right_shoulder.x)
        mouth_width = abs(mouth_left.x - mouth_right.x)

        nose_to_shoulder_y = abs(nose.y - shoulder_midpoint["y"])
        nose_to_shoulder_x = abs(nose.x - shoulder_midpoint["x"])
        angle = math.degrees(math.atan2(right_ear.y - left_ear.y, right_ear.x - left_ear.x))


        return {
            "shoulder_imbalance": shoulder_imbalance,
            "shoulder_width": shoulder_width,
            "mouth_width": mouth_width,
            "nose_to_shoulder_y": nose_to_shoulder_y,
            "nose_to_shoulder_x": nose_to_shoulder_x,
            "shoulder_mid_y": shoulder_midpoint["y"],
            "head_tilt_angle": angle,
        }
    
    def get_shoulder_imbalance(self, mp_pose): # Y is the coordinate that goes downward, we check the difference between the y coordinates of both the sides of the shoulder.
        key_points = self.get_key_points(mp_pose)

        if not key_points:
            return None

        left_shoulder = key_points["left_shoulder"]
        right_shoulder = key_points["right_shoulder"]

        imbalance = abs(left_shoulder.y - right_shoulder.y)

        return imbalance

    def get_key_points(self, mp_pose): #instead of landmark id, this gives named dictonary for readibility.
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