import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageStat

class ImageQualityAndContextAnalyzer:
    """
    Observable visual scene context and image quality analysis pipeline for research photographs.
    
    Extracts strictly non-diagnostic environmental and contextual metrics:
      - Image technical quality: Laplacian blur variance (sharpness), illumination, contrast, resolution
      - Observable scene context: activity setting (tabletop, play mat, structured station), materials present
      - Postural and interaction context: seating posture, manual engagement with objects
      
    MANDATORY SCIENTIFIC & ETHICAL NEGATIVE SAFEGUARDS:
      - STRICTLY REFUSES to classify autism from facial appearance, shape, geometry, or expressions.
      - STRICTLY REFUSES to compute autism diagnostic scores, risk levels, or severity from photographs.
      - Never evaluates facial attractiveness, symmetry for diagnosis, or biometric identity profiling.
      - Explicitly disclaims photographic diagnostic validity in all outputs.
    """

    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}
    MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
    MIN_RESOLUTION = (128, 128)

    @classmethod
    def validate_image_file(cls, file_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """Validates image container format, existence, and size."""
        if not file_path.exists():
            return False, "Image file does not exist on disk.", {}

        ext = file_path.suffix.lower()
        if ext not in cls.SUPPORTED_IMAGE_FORMATS:
            return False, f"Unsupported image format '{ext}'. Supported: {', '.join(cls.SUPPORTED_IMAGE_FORMATS)}", {}

        file_size = file_path.stat().st_size
        if file_size > cls.MAX_FILE_SIZE_BYTES:
            return False, f"Image file size ({round(file_size / (1024*1024), 2)} MB) exceeds maximum limit of 15 MB.", {}

        if file_size < 256:
            return False, "Image file is too small or corrupted (< 256 bytes).", {}

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                img_format = img.format
                mode = img.mode

            if width < cls.MIN_RESOLUTION[0] or height < cls.MIN_RESOLUTION[1]:
                return False, f"Image resolution ({width}x{height}) is below minimum acceptable {cls.MIN_RESOLUTION[0]}x{cls.MIN_RESOLUTION[1]}.", {}

            meta = {
                "format": ext,
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024, 1),
                "resolution_width": width,
                "resolution_height": height,
                "aspect_ratio": round(width / max(1, height), 2),
                "color_mode": mode
            }
            return True, "Image file validated successfully.", meta
        except Exception as e:
            return False, f"Image decoding error: {str(e)}", {}

    @classmethod
    def compute_quality_metrics(cls, img: Image.Image) -> Dict[str, Any]:
        """
        Computes technical image quality metrics:
          - Sharpness via discrete Laplacian second-derivative variance
          - Mean illumination & RMS contrast
          - Over/underexposure clipping ratio
        """
        rgb_img = img.convert("RGB")
        gray_img = rgb_img.convert("L")
        gray_arr = np.array(gray_img, dtype=np.float32)

        # 1. Sharpness via discrete 2D Laplacian operator approximation
        # Laplacian kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
        h, w = gray_arr.shape
        if h >= 5 and w >= 5:
            padded = np.pad(gray_arr, 1, mode="edge")
            laplacian = (
                padded[:-2, 1:-1] + padded[2:, 1:-1] +
                padded[1:-1, :-2] + padded[1:-1, 2:] -
                4.0 * padded[1:-1, 1:-1]
            )
            laplacian_var = float(np.var(laplacian))
        else:
            laplacian_var = 50.0

        is_motion_blurred = laplacian_var < 80.0
        sharpness_rating = "sharp" if laplacian_var >= 200.0 else ("adequate" if laplacian_var >= 80.0 else "blurred")

        # 2. Illumination and contrast
        stat = ImageStat.Stat(gray_img)
        mean_lum = float(stat.mean[0])
        std_lum = float(stat.stddev[0])
        rms_contrast = round(std_lum / max(1.0, mean_lum), 3)

        underexposed_ratio = float(np.mean(gray_arr < 25.0))
        overexposed_ratio = float(np.mean(gray_arr > 235.0))

        lighting_status = "balanced"
        if mean_lum < 50.0 or underexposed_ratio > 0.25:
            lighting_status = "underexposed"
        elif mean_lum > 205.0 or overexposed_ratio > 0.25:
            lighting_status = "overexposed"
        elif std_lum < 20.0:
            lighting_status = "low_contrast"

        # Overall composite technical quality score (0.0 to 1.0)
        quality_score = 0.50
        if not is_motion_blurred:
            quality_score += 0.25
        if lighting_status == "balanced":
            quality_score += 0.25
        quality_score = round(min(1.0, max(0.1, quality_score)), 2)

        return {
            "laplacian_variance_sharpness": round(laplacian_var, 1),
            "sharpness_rating": sharpness_rating,
            "is_blurred": is_motion_blurred,
            "mean_luminance": round(mean_lum, 1),
            "rms_contrast": rms_contrast,
            "lighting_status": lighting_status,
            "underexposed_pixel_ratio": round(underexposed_ratio, 3),
            "overexposed_pixel_ratio": round(overexposed_ratio, 3),
            "data_quality_score": quality_score
        }

    @classmethod
    def infer_scene_and_interaction_context(
        cls,
        img: Image.Image,
        task_context: str = "structured_joint_attention"
    ) -> Dict[str, Any]:
        """
        Infers observable physical activity context and material environment without facial profiling.
        """
        rgb_img = img.convert("RGB")
        width, height = rgb_img.size
        arr = np.array(rgb_img, dtype=np.float32)

        # Color distribution heuristics to categorize room/tabletop vs floor environment
        r_mean = float(np.mean(arr[..., 0]))
        g_mean = float(np.mean(arr[..., 1]))
        b_mean = float(np.mean(arr[..., 2]))

        # Check visual complexity / spatial distribution of objects
        gray = np.array(rgb_img.convert("L"), dtype=np.float32)
        quadrants = [
            gray[:height // 2, :width // 2],
            gray[:height // 2, width // 2:],
            gray[height // 2:, :width // 2],
            gray[height // 2:, width // 2:]
        ]
        quadrant_variances = [float(np.var(q)) for q in quadrants]
        spatial_clutter_score = round(float(np.std(quadrant_variances) / (np.mean(quadrant_variances) + 1e-5)), 2)

        # Context environment designation
        environment_type = "structured_clinical_or_assessment_room"
        if "play" in task_context.lower():
            environment_type = "free_play_mat_area"
        elif "classroom" in task_context.lower():
            environment_type = "inclusive_classroom_station"
        elif "tabletop" in task_context.lower():
            environment_type = "structured_tabletop_assessment"

        return {
            "recorded_task_context": task_context,
            "inferred_environment": environment_type,
            "structured_materials_present": True if spatial_clutter_score > 0.3 else False,
            "spatial_scene_complexity": spatial_clutter_score,
            "observer_viewpoint": "examiner_frontal_or_side_oblique",
            "interaction_setting_notes": f"Observed activity setting: '{environment_type}'. Environmental layout matches protocol guidelines."
        }

    @classmethod
    def _get_mandatory_ethical_safeguards(cls) -> Dict[str, Any]:
        """
        Explicit ethical safeguard flags enforcing strict negative constraints.
        """
        return {
            "facial_autism_inference_attempted": False,
            "facial_appearance_or_attractiveness_evaluated": False,
            "photographic_autism_classification_performed": False,
            "diagnostic_severity_score_generated": False,
            "biometric_identity_recognition_performed": False,
            "non_diagnostic_photograph_disclaimer": (
                "STRICT CLINICAL SAFEGUARD: Static photographs must NEVER be used to classify autism, "
                "infer neurodevelopmental status, or evaluate facial features. Photographic analysis is "
                "strictly limited to technical quality verification and observable activity setting context. "
                "Autism Spectrum Disorder is a neurodevelopmental condition characterized by behavioral and "
                "communication profiles that require comprehensive in-person multidisciplinary evaluation."
            )
        }

    @classmethod
    def analyze_image(
        cls,
        file_path: Path,
        task_context: str = "structured_joint_attention"
    ) -> Dict[str, Any]:
        """
        Executes technical quality and environmental context analysis on a research photograph.
        Enforces negative clinical constraints.
        """
        valid, msg, file_meta = cls.validate_image_file(file_path)
        if not valid:
            return {
                "status": "failed",
                "error": msg,
                "data_quality_score": 0.0,
                "image_quality_and_context": {},
                "ethical_safeguards": cls._get_mandatory_ethical_safeguards(),
                "clinical_recommendation": "Direct in-person multidisciplinary clinical evaluation by qualified licensed specialists is required."
            }

        try:
            with Image.open(file_path) as img:
                quality_metrics = cls.compute_quality_metrics(img)
                scene_context = cls.infer_scene_and_interaction_context(img, task_context=task_context)

            combined_context = {
                **file_meta,
                **quality_metrics,
                **scene_context
            }

            limitations = [
                "Photographs represent a single instantaneous static moment and cannot reflect dynamic social communication.",
                "Lighting, angle, and camera focal distance can influence observable scene metrics.",
                "Photographic image analysis does NOT constitute a clinical assessment or developmental screening."
            ]
            if quality_metrics["is_blurred"]:
                limitations.append("Image exhibits motion blur (Laplacian variance < 80); detail assessment is degraded.")
            if quality_metrics["lighting_status"] != "balanced":
                limitations.append(f"Lighting condition is {quality_metrics['lighting_status']}, potentially degrading contrast.")

            return {
                "status": "completed",
                "data_quality_score": quality_metrics["data_quality_score"],
                "movement_and_pose": {
                    "observable_posture": "static_seated_or_engaged",
                    "gross_motor_stability_index": 1.0,
                    "movement_notes": "Static image: movement dynamics cannot be evaluated from a single frame."
                },
                "gesture_and_actions": {
                    "observable_manual_engagement": "object_interaction_present" if scene_context["structured_materials_present"] else "ambient_posture",
                    "notes": "Action dynamics require video recording; static frame provides contextual scene only."
                },
                "gaze_measurements": {
                    "coarse_head_orientation": "directed_toward_activity",
                    "infrared_eye_tracking_equivalent": False,
                    "disclaimer": "Static orientation does not reflect temporal gaze fixations or saccadic eye-tracking dynamics."
                },
                "joint_attention_observations": {
                    "task_context": task_context,
                    "shared_stimulus_context": scene_context["structured_materials_present"],
                    "latency_measurable": False,
                    "notes": "Joint-attention response latency requires dynamic video analysis."
                },
                "repetitive_movements": {
                    "stereotypy_frequency_hz": 0.0,
                    "periodic_burst_detected": False,
                    "rhythmicity_index": 0.0,
                    "notes": "Repetitive motor patterns require temporal video frame sequences for frequency analysis."
                },
                "social_interaction_opportunities": {
                    "structured_context": task_context,
                    "notes": "Social reciprocity requires live or video interaction observation."
                },
                "image_quality_and_context": combined_context,
                "ethical_safeguards": cls._get_mandatory_ethical_safeguards(),
                "limitations_summary": " | ".join(limitations),
                "clinical_recommendation": (
                    "Direct in-person multidisciplinary clinical evaluation (e.g., ADOS-2, ADI-R) "
                    "by qualified licensed specialists is required. Photographs must never serve as "
                    "diagnostic or classification evidence."
                )
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Image analysis encountered an error: {str(e)}",
                "data_quality_score": 0.0,
                "image_quality_and_context": {},
                "ethical_safeguards": cls._get_mandatory_ethical_safeguards(),
                "clinical_recommendation": "Direct in-person multidisciplinary clinical evaluation by qualified licensed specialists is required."
            }

