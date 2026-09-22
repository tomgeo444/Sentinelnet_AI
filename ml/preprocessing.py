"""
SentinelNet AI - Data Preprocessing and Feature Normalization Pipeline
Ensures strict parity between training transformations and live inference.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from capture.feature_extractor import FEATURE_COLUMNS

logger = logging.getLogger("sentinelnet.ml.preprocessing")


class PreprocessingPipeline:
    """
    Standardizes feature vectors and encodes target labels.
    Persists scaler and encoder artifacts for low-latency live inference.
    """
    def __init__(self, scaler=None, label_encoder=None, feature_names=None):
        self.scaler = scaler or StandardScaler()
        self.label_encoder = label_encoder or LabelEncoder()
        self.feature_names = feature_names or FEATURE_COLUMNS
        self.is_fitted = False

    def fit(self, X: pd.DataFrame | np.ndarray, y: pd.Series | np.ndarray = None):
        """Fits scaler on feature matrix and label encoder on class labels."""
        if isinstance(X, pd.DataFrame):
            X_mat = X[self.feature_names].values
        else:
            X_mat = X

        # Replace any residual NaNs or Infs
        X_mat = np.nan_to_num(X_mat, nan=0.0, posinf=1e6, neginf=-1e6)
        self.scaler.fit(X_mat)

        if y is not None:
            self.label_encoder.fit(y)

        self.is_fitted = True
        return self

    def transform_features(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Transforms feature matrix using fitted scaler."""
        if not self.is_fitted:
            raise RuntimeError("PreprocessingPipeline is not fitted.")

        if isinstance(X, pd.DataFrame):
            # Align columns precisely
            for col in self.feature_names:
                if col not in X.columns:
                    X[col] = 0.0
            X_mat = X[self.feature_names].values
        else:
            X_mat = X

        X_mat = np.nan_to_num(X_mat, nan=0.0, posinf=1e6, neginf=-1e6)
        return self.scaler.transform(X_mat).astype(np.float32)

    def transform_labels(self, y: pd.Series | np.ndarray | list) -> np.ndarray:
        """Encodes string class labels into numerical indices."""
        if not self.is_fitted:
            raise RuntimeError("PreprocessingPipeline is not fitted.")
        return self.label_encoder.transform(y)

    def inverse_transform_label(self, class_idx: int) -> str:
        """Decodes integer class index back to string label."""
        return self.label_encoder.inverse_transform([class_idx])[0]

    def transform_single_flow(self, flow_features: dict) -> np.ndarray:
        """
        Transforms a single extracted live flow dictionary into a scaled numpy vector.
        Returns shape: (1, num_features, 1) ready for 1D-CNN tensor inference.
        """
        raw_vec = np.array([[float(flow_features.get(col, 0.0)) for col in self.feature_names]], dtype=np.float32)
        raw_vec = np.nan_to_num(raw_vec, nan=0.0, posinf=1e6, neginf=-1e6)
        scaled_vec = self.scaler.transform(raw_vec).astype(np.float32)
        # Reshape to (1, num_features, 1) for Conv1D
        return np.expand_dims(scaled_vec, axis=-1)

    def save(
        self,
        scaler_path: str = "models/scaler.joblib",
        encoder_path: str = "models/label_encoder.joblib",
        features_path: str = "models/feature_names.json",
    ):
        """Serializes preprocessor artifacts to disk."""
        os.makedirs(os.path.dirname(scaler_path) or ".", exist_ok=True)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.label_encoder, encoder_path)
        with open(features_path, "w") as f:
            json.dump(self.feature_names, f, indent=2)
        logger.info(f"Saved preprocessing artifacts to: {scaler_path}, {encoder_path}, {features_path}")

    @classmethod
    def load(
        cls,
        scaler_path: str = "models/scaler.joblib",
        encoder_path: str = "models/label_encoder.joblib",
        features_path: str = "models/feature_names.json",
    ):
        """Loads serialized preprocessor artifacts from disk."""
        if not (os.path.exists(scaler_path) and os.path.exists(encoder_path) and os.path.exists(features_path)):
            raise FileNotFoundError("Preprocessing artifacts missing.")

        scaler = joblib.load(scaler_path)
        encoder = joblib.load(encoder_path)
        with open(features_path, "r") as f:
            feature_names = json.load(f)

        pipeline = cls(scaler=scaler, label_encoder=encoder, feature_names=feature_names)
        pipeline.is_fitted = True
        return pipeline
