"""
Unit tests for Deep Learning Model architectures and inference.
"""

import torch
import pytest
from ml.model import SentinelNet1DCNN, SentinelNetMLP
from ml.predictor import SentinelNetPredictor


def test_1dcnn_architecture():
    batch_size = 8
    num_features = 22
    num_classes = 5

    model = SentinelNet1DCNN(num_features=num_features, num_classes=num_classes)
    x = torch.randn(batch_size, 1, num_features)
    logits = model(x)

    assert logits.shape == (batch_size, num_classes)

    probs = model.predict_probabilities(x)
    assert probs.shape == (batch_size, num_classes)
    # Check sum to 1
    assert torch.allclose(probs.sum(dim=-1), torch.ones(batch_size), atol=1e-4)


def test_mlp_architecture():
    batch_size = 4
    num_features = 22
    num_classes = 5

    mlp = SentinelNetMLP(num_features=num_features, num_classes=num_classes)
    x = torch.randn(batch_size, num_features)
    logits = mlp(x)

    assert logits.shape == (batch_size, num_classes)


def test_predictor_fallback_when_unloaded():
    predictor = SentinelNetPredictor(model_path="nonexistent_model.pt")
    dummy_feat = {"flow_duration": 1.0, "total_fwd_packets": 5}
    pred = predictor.predict_flow(dummy_feat)

    assert "prediction" in pred
    assert "confidence" in pred
    assert "is_attack" in pred
