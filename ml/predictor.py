"""
SentinelNet AI - Deep Learning Inference Engine
Thread-safe prediction pipeline applying identical transformations to live flows.
"""

import os
import json
import logging
import torch
import numpy as np
from ml.model import SentinelNet1DCNN
from ml.preprocessing import PreprocessingPipeline

logger = logging.getLogger("sentinelnet.ml.predictor")


class SentinelNetPredictor:
    """
    Loads trained deep learning model and preprocessor to perform real-time flow inference.
    """
    def __init__(
        self,
        model_path: str = "models/sentinelnet_model.pt",
        scaler_path: str = "models/scaler.joblib",
        encoder_path: str = "models/label_encoder.joblib",
        features_path: str = "models/feature_names.json",
        metrics_path: str = "models/model_metrics.json",
    ):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.encoder_path = encoder_path
        self.features_path = features_path
        self.metrics_path = metrics_path

        self.model = None
        self.preprocessor = None
        self.classes = []
        self.feature_names = []
        self.metrics = {}
        self.is_loaded = False

        self._load_artifacts()

    def _load_artifacts(self):
        """Loads model weights, scalers, and label encoders."""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model checkpoint not found at: {self.model_path}. Model not yet loaded.")
            return

        try:
            # 1. Load Preprocessor
            self.preprocessor = PreprocessingPipeline.load(
                scaler_path=self.scaler_path,
                encoder_path=self.encoder_path,
                features_path=self.features_path,
            )
            self.classes = list(self.preprocessor.label_encoder.classes_)
            self.feature_names = self.preprocessor.feature_names

            # 2. Load Model Architecture & Checkpoint
            checkpoint = torch.load(self.model_path, map_location="cpu")
            num_features = checkpoint.get("num_features", len(self.feature_names))
            num_classes = checkpoint.get("num_classes", len(self.classes))

            self.model = SentinelNet1DCNN(num_features=num_features, num_classes=num_classes)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.eval()

            # 3. Load Metrics if present
            if os.path.exists(self.metrics_path):
                with open(self.metrics_path, "r") as f:
                    self.metrics = json.load(f)

            self.is_loaded = True
            logger.info(f"SentinelNet Deep Learning model loaded successfully. Classes: {self.classes}")
        except Exception as e:
            logger.error(f"Failed to load ML artifacts: {e}", exc_info=True)
            self.is_loaded = False

    def predict_flow(self, flow_features: dict) -> dict:
        """
        Executes live inference on a flow feature dictionary.
        Returns:
            - prediction: str ("BENIGN", "DoS_DDoS", etc.)
            - attack_type: str
            - is_attack: bool
            - confidence: float (0.0 - 1.0)
            - probabilities: dict[str, float]
        """
        if not self.is_loaded or self.model is None or self.preprocessor is None:
            # Fallback heuristic if model is not loaded yet
            return {
                "prediction": "BENIGN",
                "attack_type": "BENIGN",
                "is_attack": False,
                "confidence": 0.50,
                "probabilities": {"BENIGN": 0.50},
            }

        # Transform features identically to training
        input_tensor = self.preprocessor.transform_single_flow(flow_features)  # (1, num_features, 1)
        torch_tensor = torch.tensor(input_tensor, dtype=torch.float32)

        with torch.no_grad():
            outputs = self.model(torch_tensor)
            probs = torch.softmax(outputs, dim=1).squeeze(0).numpy()

        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])
        predicted_class = self.preprocessor.inverse_transform_label(top_idx)
        is_attack = (predicted_class != "BENIGN")

        prob_dict = {
            cls_name: round(float(probs[i]), 4)
            for i, cls_name in enumerate(self.classes)
        }

        return {
            "prediction": predicted_class,
            "attack_type": predicted_class,
            "is_attack": is_attack,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
        }

    def get_model_info(self) -> dict:
        """Returns metadata about the loaded model and test evaluation metrics."""
        return {
            "is_loaded": self.is_loaded,
            "architecture": "1D Convolutional Neural Network + Dense Classifier (PyTorch)",
            "dataset": "CICIDS2017 Benchmark Flow Distribution",
            "features_count": len(self.feature_names) if self.feature_names else 22,
            "classes_count": len(self.classes) if self.classes else 5,
            "classes": self.classes,
            "feature_names": self.feature_names,
            "metrics": self.metrics,
        }
