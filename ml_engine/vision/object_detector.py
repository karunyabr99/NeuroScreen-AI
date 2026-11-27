from pathlib import Path
from typing import Any, Dict

import cv2
from ultralytics import YOLO


class ObjectDetector:
    """
    Detects visible objects in video frames.
    This is general object detection, not autism screening.
    """

    MODEL_PATH = Path(__file__).parent / "models" / "yolo11n.pt"

    @classmethod
    def analyze_video(
        cls,
        video_path: str,
        sample_fps: float = 2.0
    ) -> Dict[str, Any]:

        path = Path(video_path)

        if not path.is_file():
            return {"status": "error", "message": "Video not found"}

        if sample_fps <= 0:
            return {"status": "error", "message": "Invalid sample_fps"}

        if not cls.MODEL_PATH.is_file():
            return {
                "status": "error",
                "message": "YOLO model file not found"
            }

        model = YOLO(str(cls.MODEL_PATH))
        cap = cv2.VideoCapture(str(path))

        if not cap.isOpened():
            return {"status": "error", "message": "Cannot open video"}

        fps = cap.get(cv2.CAP_PROP_FPS)

        if not fps or fps <= 0:
            cap.release()
            return {"status": "error", "message": "Invalid video FPS"}

        interval = max(1, round(fps / sample_fps))
        frame_no = 0
        frames_sampled = 0
        detections = {}

        try:
            while True:
                ok, frame = cap.read()

                if not ok:
                    break

                if frame_no % interval == 0:
                    results = model.predict(
                        frame,
                        verbose=False,
                        conf=0.35
                    )

                    frames_sampled += 1

                    for result in results:
                        for box in result.boxes:
                            class_id = int(box.cls[0].item())
                            label = model.names[class_id]

                            detections[label] = (
                                detections.get(label, 0) + 1
                            )

                frame_no += 1

        finally:
            cap.release()

        return {
            "status": "completed",
            "frames_sampled": frames_sampled,
            "detected_objects": detections,
            "model": "YOLO11n pretrained general object detector",
            "clinical_interpretation": "not_performed"
        }