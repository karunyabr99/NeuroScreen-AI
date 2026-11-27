from pathlib import Path
from typing import Any, Dict

import cv2
import mediapipe as mp
import numpy as np


class GestureAnalyzer:
    """
    Measures hand landmark movement over time.

    This module measures motion patterns only.
    It does not diagnose autism or classify clinical gestures.
    """

    MODEL_PATH = (
        Path(__file__).parent / "models" / "hand_landmarker.task"
    )

    @classmethod
    def analyze_video(
        cls,
        video_path: str,
        sample_fps: float = 5.0
    ) -> Dict[str, Any]:

        path = Path(video_path)

        if not path.is_file():
            return {"status": "error", "message": "Video file not found"}

        if not cls.MODEL_PATH.is_file():
            return {"status": "error", "message": "Hand model not found"}

        if sample_fps <= 0:
            return {"status": "error", "message": "sample_fps must be positive"}

        cap = cv2.VideoCapture(str(path))

        if not cap.isOpened():
            return {"status": "error", "message": "Cannot open video"}

        fps = cap.get(cv2.CAP_PROP_FPS)

        if not fps or fps <= 0:
            cap.release()
            return {"status": "error", "message": "Invalid video frame rate"}

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(cls.MODEL_PATH)
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2
        )

        sampled_frames = 0
        detected_frames = 0
        motion_values = []
        previous_positions = None
        last_timestamp = -1
        frame_interval = max(1, round(fps / sample_fps))
        frame_no = 0

        try:
            with mp.tasks.vision.HandLandmarker.create_from_options(
                options
            ) as detector:

                while True:
                    ok, frame = cap.read()

                    if not ok:
                        break

                    if frame_no % frame_interval == 0:
                        rgb = cv2.cvtColor(
                            frame, cv2.COLOR_BGR2RGB
                        )

                        image = mp.Image(
                            image_format=mp.ImageFormat.SRGB,
                            data=rgb
                        )

                        timestamp = int(frame_no * 1000 / fps)
                        timestamp = max(timestamp, last_timestamp + 1)
                        last_timestamp = timestamp

                        result = detector.detect_for_video(
                            image, timestamp
                        )

                        sampled_frames += 1

                        current_positions = []

                        if result.hand_landmarks:
                            detected_frames += 1

                            for hand in result.hand_landmarks:
                                wrist = hand[0]
                                current_positions.append(
                                    np.array([wrist.x, wrist.y])
                                )

                            if previous_positions is not None:
                                for current in current_positions:
                                    distances = [
                                        np.linalg.norm(current - previous)
                                        for previous in previous_positions
                                    ]

                                    if distances:
                                        motion_values.append(
                                            float(min(distances))
                                        )

                            previous_positions = current_positions

                    frame_no += 1

        finally:
            cap.release()

        average_motion = (
            round(float(np.mean(motion_values)), 5)
            if motion_values else None
        )

        return {
            "status": "completed",
            "frames_sampled": sampled_frames,
            "frames_with_hands": detected_frames,
            "hand_detection_coverage_percent": round(
                detected_frames / sampled_frames * 100, 2
            ) if sampled_frames else 0,
            "average_wrist_position_change": average_motion,
            "motion_measurement": (
                "Normalized wrist-position change between sampled frames; "
                "not a validated gesture classification."
            ),
            "gesture_classification": "not_implemented",
            "clinical_interpretation": "not_performed"
        }