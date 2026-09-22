"""
Unit tests for Data Preprocessing and Normalization Pipeline.
"""

import os
import pytest
import numpy as np
import pandas as pd
from ml.preprocessing import PreprocessingPipeline
from ml.dataset import generate_benchmark_flow_data
from capture.feature_extractor import FEATURE_COLUMNS


def test_preprocessing_fit_transform():
    df = generate_benchmark_flow_data(num_samples=200)
    pipeline = PreprocessingPipeline(feature_names=FEATURE_COLUMNS)
    pipeline.fit(df[FEATURE_COLUMNS], df["label"])

    assert pipeline.is_fitted
    assert len(pipeline.label_encoder.classes_) == 5

    X_trans = pipeline.transform_features(df[FEATURE_COLUMNS])
    y_trans = pipeline.transform_labels(df["label"])

    assert X_trans.shape == (200, 22)
    assert y_trans.shape == (200,)
    assert not np.isnan(X_trans).any()


def test_single_flow_transformation():
    df = generate_benchmark_flow_data(num_samples=100)
    pipeline = PreprocessingPipeline(feature_names=FEATURE_COLUMNS)
    pipeline.fit(df[FEATURE_COLUMNS], df["label"])

    sample_dict = df[FEATURE_COLUMNS].iloc[0].to_dict()
    vec_3d = pipeline.transform_single_flow(sample_dict)

    # Check shape for 1D-CNN: (1, 22, 1)
    assert vec_3d.shape == (1, 22, 1)
    assert isinstance(vec_3d, np.ndarray)


def test_preprocessor_serialization(tmp_path):
    df = generate_benchmark_flow_data(num_samples=100)
    pipeline = PreprocessingPipeline(feature_names=FEATURE_COLUMNS)
    pipeline.fit(df[FEATURE_COLUMNS], df["label"])

    scaler_p = str(tmp_path / "scaler.joblib")
    encoder_p = str(tmp_path / "encoder.joblib")
    features_p = str(tmp_path / "features.json")

    pipeline.save(scaler_p, encoder_p, features_p)
    loaded = PreprocessingPipeline.load(scaler_p, encoder_p, features_p)

    assert loaded.is_fitted
    assert list(loaded.label_encoder.classes_) == list(pipeline.label_encoder.classes_)
