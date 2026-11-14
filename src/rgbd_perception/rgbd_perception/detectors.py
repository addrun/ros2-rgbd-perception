# SPDX-License-Identifier: AGPL-3.0-only
"""Optional model adapters. Heavy libraries are only imported for real inference."""
from dataclasses import dataclass
from pathlib import Path
import os
import sys


@dataclass(frozen=True)
class Box:
    xyxy: list
    score: float
    label: str


class FixtureDetector:
    """Known synthetic rectangle, used only by the explicitly enabled offline demo."""
    def predict(self, image):
        if image.shape[:2] != (480, 640):
            raise ValueError("fixture backend requires the 640x480 synthetic demo")
        return [Box([180, 180, 460, 300], 1., "synthetic_target")]


class UltralyticsDetector:
    def __init__(self, model_path, confidence):
        if not Path(model_path).is_file():
            raise ValueError("model_path must be an existing local weight file")
        from ultralytics import YOLO
        self.model = YOLO(model_path)
        self.confidence = confidence

    def predict(self, image):
        result = self.model.predict(image, conf=self.confidence, verbose=False)[0]
        return [Box(b.xyxy[0].cpu().tolist(), float(b.conf.item()), result.names[int(b.cls.item())])
                for b in result.boxes]


class YoloV5Detector:
    """Adapter for a user-provided, compatible upstream YOLOv5 checkout and weights."""
    def __init__(self, repo, model_path, confidence):
        path = Path(repo).expanduser().resolve()
        if not (path / "models/common.py").is_file() or not Path(model_path).is_file():
            raise ValueError("yolov5_repo and model_path must point to existing YOLOv5 code and weights")
        os.environ.setdefault("YOLOv5_AUTOINSTALL", "false")
        os.environ.setdefault("YOLO_AUTOINSTALL", "False")
        sys.path.insert(0, str(path))
        import torch
        from models.common import DetectMultiBackend
        from utils.augmentations import letterbox
        from utils.general import non_max_suppression, scale_boxes
        self.torch = torch
        self.model = DetectMultiBackend(model_path, device=torch.device("cpu"))
        self.letterbox = letterbox
        self.nms = non_max_suppression
        self.scale_boxes = scale_boxes
        self.confidence = confidence

    def predict(self, image):
        img = self.letterbox(image, (640, 640), stride=32, auto=True)[0]
        tensor = self.torch.from_numpy(img.transpose((2, 0, 1))[::-1].copy()).float() / 255
        with self.torch.inference_mode():
            detections = self.nms(self.model(tensor.unsqueeze(0)), self.confidence, .45)[0]
            detections[:, :4] = self.scale_boxes(tensor.shape[1:], detections[:, :4], image.shape).round()
        return [Box(row[:4].tolist(), float(row[4]), self.model.names[int(row[5])])
                for row in detections.cpu()]
