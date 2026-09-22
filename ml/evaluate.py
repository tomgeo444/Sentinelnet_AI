"""
SentinelNet AI - Model Evaluation & Performance Reporting
Generates real academic metrics: Precision, Recall, F1, Accuracy, and Confusion Matrix.
"""

import os
import json
import logging
import torch
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

logger = logging.getLogger("sentinelnet.ml.evaluate")


def evaluate_test_set(model, test_loader, preprocessor, device=torch.device("cpu"), metrics_save_path="models/model_metrics.json") -> dict:
    """Evaluates the model on test DataLoader, computes metrics, and generates confusion matrix visualization."""
    model.eval()
    all_preds = []
    all_targets = []
    all_probs = []

    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(device)
            outputs = model(batch_x)
            probs = torch.softmax(outputs, dim=1)
            preds = outputs.argmax(dim=1)

            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.numpy())
            all_probs.extend(probs.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    all_probs = np.array(all_probs)

    target_names = list(preprocessor.label_encoder.classes_)

    # Compute Metrics
    acc = float(accuracy_score(all_targets, all_preds))
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(all_targets, all_preds, average="macro", zero_division=0)
    prec_weighted, rec_weighted, f1_weighted, _ = precision_recall_fscore_support(all_targets, all_preds, average="weighted", zero_division=0)
    
    prec_per_class, rec_per_class, f1_per_class, support_per_class = precision_recall_fscore_support(all_targets, all_preds, average=None, zero_division=0)

    per_class_metrics = {}
    for i, name in enumerate(target_names):
        per_class_metrics[name] = {
            "precision": round(float(prec_per_class[i]), 4),
            "recall": round(float(rec_per_class[i]), 4),
            "f1_score": round(float(f1_per_class[i]), 4),
            "support": int(support_per_class[i]),
        }

    conf_mat = confusion_matrix(all_targets, all_preds)

    metrics_payload = {
        "dataset_name": "CICIDS2017 Benchmark Flow Distribution",
        "model_architecture": "1D-CNN + Dense Residual Classifier",
        "num_features": len(preprocessor.feature_names),
        "num_classes": len(target_names),
        "classes": target_names,
        "test_samples": len(all_targets),
        "overall": {
            "accuracy": round(acc, 4),
            "precision_macro": round(float(prec_macro), 4),
            "recall_macro": round(float(rec_macro), 4),
            "f1_macro": round(float(f1_macro), 4),
            "precision_weighted": round(float(prec_weighted), 4),
            "recall_weighted": round(float(rec_weighted), 4),
            "f1_weighted": round(float(f1_weighted), 4),
        },
        "per_class": per_class_metrics,
        "confusion_matrix": conf_mat.tolist(),
    }

    # Save metrics JSON
    os.makedirs(os.path.dirname(metrics_save_path) or ".", exist_ok=True)
    with open(metrics_save_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    logger.info(f"Saved evaluation metrics to: {metrics_save_path}")

    # Plot and Save Confusion Matrix
    try:
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            conf_mat,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=target_names,
            yticklabels=target_names
        )
        plt.title("SentinelNet AI - Confusion Matrix (Test Set)")
        plt.xlabel("Predicted Label")
        plt.ylabel("Ground Truth Label")
        plt.tight_layout()
        cm_path = "models/confusion_matrix.png"
        plt.savefig(cm_path, dpi=200)
        plt.close()
        logger.info(f"Saved confusion matrix visualization to: {cm_path}")
    except Exception as e:
        logger.warning(f"Could not save confusion matrix plot: {e}")

    # Console display
    report_str = classification_report(all_targets, all_preds, target_names=target_names, digits=4)
    print("\n" + "=" * 65)
    print("           SENTINELNET AI - MODEL EVALUATION REPORT")
    print("=" * 65)
    print(report_str)
    print(f"Overall Accuracy: {acc * 100:.2f}%\n" + "=" * 65 + "\n")

    return metrics_payload
