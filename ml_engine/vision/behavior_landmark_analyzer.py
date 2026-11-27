from pathlib import Path
from typing import Any, Dict

import cv2
import mediapipe as mp


class BehaviorLandmarkAnalyzer:
    """Extracts real pose, hand, and face landmark detection measurements.

    This module does not diagnose autism or classify facial appearance,
    emotions, gestures, or social attention.
    """

    MODEL_DIR = Path(__file__).resolve().parent / "models"

    POSE_MODEL = MODEL_DIR / "pose_landmarker_lite.task"
    HAND_MODEL = MODEL_DIR / "hand_landmarker.task"
    FACE_MODEL = MODEL_DIR / "face_landmarker.task"

    LEFT_EYE_CORNERS = [33, 133]
    RIGHT_EYE_CORNERS = [362, 263]

    LEFT_IRIS = [468, 469, 470, 471, 472]
    RIGHT_IRIS = [473, 474, 475, 476, 477]

    @classmethod
    def analyze_video(
        cls,
        video_path: str,
        sample_fps: float = 5.0
    ) -> Dict[str, Any]:

        video_path = Path(video_path)

        if not video_path.is_file():
            raise FileNotFoundError(f"Video not found: {video_path}")

        for model_path in [cls.POSE_MODEL, cls.HAND_MODEL, cls.FACE_MODEL]:
            if not model_path.is_file():
                raise FileNotFoundError(f"MediaPipe model missing: {model_path}")

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError("Could not open video file")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 30.0

        sample_every = max(1, round(fps / sample_fps))

        base_options = mp.tasks.BaseOptions

        pose_options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=base_options(
                model_asset_path=str(cls.POSE_MODEL)
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1
        )

        hand_options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options(
                model_asset_path=str(cls.HAND_MODEL)
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.2,
            min_hand_presence_confidence=0.2
        )

        face_options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options(
                model_asset_path=str(cls.FACE_MODEL)
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=1
        )

        pose_detector = None
        hand_detector = None
        face_detector = None

        frame_no = 0
        frames_checked = 0
        pose_frames = 0
        hand_frames = 0
        face_frames = 0
        iris_frames = 0
        left_iris_positions = []
        right_iris_positions = []

        total_hands = 0
        total_pose_landmarks = 0
        total_face_landmarks = 0

        try:
            pose_detector = (
                mp.tasks.vision.PoseLandmarker.create_from_options(
                    pose_options
                )
            )
            hand_detector = (
                mp.tasks.vision.HandLandmarker.create_from_options(
                    hand_options
                )
            )
            face_detector = (
                mp.tasks.vision.FaceLandmarker.create_from_options(
                    face_options
                )
            )

            while True:
                ok, frame = cap.read()

                if not ok:
                    break

                if frame_no % sample_every == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = mp.Image(
                        image_format=mp.ImageFormat.SRGB,
                        data=rgb
                    )

                    timestamp_ms = int(frame_no * 1000 / fps)

                    pose_result = pose_detector.detect_for_video(
                        image, timestamp_ms
                    )
                    hand_result = hand_detector.detect_for_video(
                        image, timestamp_ms
                    )
                    face_result = face_detector.detect_for_video(
                        image, timestamp_ms
                    )

                    frames_checked += 1

                    if pose_result.pose_landmarks:
                        pose_frames += 1
                        total_pose_landmarks += len(
                            pose_result.pose_landmarks[0]
                        )

                    if hand_result.hand_landmarks:
                        hand_frames += 1
                        total_hands += len(hand_result.hand_landmarks)

                    if face_result.face_landmarks:
                        face_frames += 1
                        points = face_result.face_landmarks[0]

                        total_face_landmarks += len(points)

                        if len(points) >= 478:
                           left_x1 = points[33].x
                           left_x2 = points[133].x
                           left_iris_x = sum(points[i].x for i in cls.LEFT_IRIS) / 5

                           right_x1 = points[362].x
                           right_x2 = points[263].x
                           right_iris_x = sum(points[i].x for i in cls.RIGHT_IRIS) / 5

                           left_width = left_x2 - left_x1
                           right_width = right_x2 - right_x1

                           if abs(left_width) > 1e-6 and abs(right_width) > 1e-6:
                              left_iris_positions.append(
                              (left_iris_x - left_x1) / left_width
                              )
                              right_iris_positions.append(
                              (right_iris_x - right_x1) / right_width
                              )
                              iris_frames += 1

                frame_no += 1

        finally:
            cap.release()

            if pose_detector:
                pose_detector.close()
            if hand_detector:
                hand_detector.close()
            if face_detector:
                face_detector.close()

        def percentage(count: int) -> float:
            return round(count / frames_checked * 100, 2) if frames_checked else 0.0

        return {
            "status": "completed" if frames_checked else "no_frames",
            "frames_checked": frames_checked,
            "sampling_fps": sample_fps,
            "pose": {
                "frames_detected": pose_frames,
                "detection_coverage_percent": percentage(pose_frames),
                "total_landmarks_detected": total_pose_landmarks
            },
            "hands": {
                "frames_detected": hand_frames,
                "detection_coverage_percent": percentage(hand_frames),
                "total_hands_detected": total_hands
            },
            "face": {
                "frames_detected": face_frames,
                "detection_coverage_percent": percentage(face_frames),
                "total_landmarks_detected": total_face_landmarks
            },
            "eye_gaze_estimation": {
            "status": "experimental_geometric_measurement",
            "frames_with_iris_measurements": iris_frames,
            "left_eye_normalized_position_mean": (
                round(sum(left_iris_positions) / len(left_iris_positions), 4)
                  if left_iris_positions else None
            ),
            "right_eye_normalized_position_mean": (
                round(sum(right_iris_positions) / len(right_iris_positions), 4)
                  if right_iris_positions else None
            ),
            "clinical_gaze_estimation": False
        },
            "gesture_recognition": "not_implemented",
            "eye_gaze_estimation": {
    "status": "experimental_geometric_measurement",
    "frames_with_iris_measurements": iris_frames,
    "left_eye_normalized_position_mean": (
        round(sum(left_iris_positions) / len(left_iris_positions), 4)
        if left_iris_positions else None
    ),
    "right_eye_normalized_position_mean": (
        round(sum(right_iris_positions) / len(right_iris_positions), 4)
        if right_iris_positions else None
    ),
    "clinical_gaze_estimation": False
},
            "object_detection": "not_implemented",
            "clinical_interpretation": "not_performed",
            "disclaimer": (
                "Landmark detection measures visibility only. "
                "It does not diagnose autism or establish developmental ability."
            )
        }
