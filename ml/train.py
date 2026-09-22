"""
SentinelNet AI - Deep Learning Model Training Pipeline
Trains the 1D-CNN classifier on network intrusion flow features with class weight balancing.
"""

import os
import json
import logging
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

from ml.dataset import load_dataset, ATTACK_CLASSES
from ml.preprocessing import PreprocessingPipeline
from ml.model import SentinelNet1DCNN
from capture.feature_extractor import FEATURE_COLUMNS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sentinelnet.ml.train")


def train_model(
    data_path: str = "data/benchmark_nids_flows.csv",
    model_save_path: str = "models/sentinelnet_model.pt",
    metrics_save_path: str = "models/model_metrics.json",
    epochs: int = 15,
    batch_size: int = 64,
    learning_rate: float = 0.001,
    random_state: int = 42,
):
    """Executes end-to-end model training, validation, and evaluation pipeline."""
    logger.info("Initializing SentinelNet AI training pipeline...")
    os.makedirs("models", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # 1. Load Data
    df = load_dataset(csv_path=data_path, generate_if_missing=True)
    logger.info(f"Loaded dataset containing {len(df)} total flow records.")

    # 2. Preprocess & Fit Scaler / Encoder
    preprocessor = PreprocessingPipeline(feature_names=FEATURE_COLUMNS)
    preprocessor.fit(X=df[FEATURE_COLUMNS], y=df["label"])
    preprocessor.save(
        scaler_path="models/scaler.joblib",
        encoder_path="models/label_encoder.joblib",
        features_path="models/feature_names.json"
    )

    X_all = preprocessor.transform_features(df[FEATURE_COLUMNS])
    y_all = preprocessor.transform_labels(df["label"])

    num_classes = len(preprocessor.label_encoder.classes_)
    num_features = len(FEATURE_COLUMNS)
    logger.info(f"Features: {num_features}, Target Classes ({num_classes}): {list(preprocessor.label_encoder.classes_)}")

    # 3. Stratified Split: 70% Train, 15% Validation, 15% Test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X_all, y_all, test_size=0.30, random_state=random_state, stratify=y_all
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=random_state, stratify=y_temp
    )

    logger.info(f"Dataset Splits -> Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # 4. Handle Class Imbalance with Loss Class Weights
    class_weights_arr = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(num_classes),
        y=y_train
    )
    class_weights_tensor = torch.tensor(class_weights_arr, dtype=torch.float32)
    logger.info(f"Balanced class weights: {dict(zip(preprocessor.label_encoder.classes_, np.round(class_weights_arr, 3)))}")

    # 5. Build DataLoaders (Reshape for 1D-CNN: batch_size, 1, num_features)
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32).unsqueeze(1), torch.tensor(y_train, dtype=torch.long))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32).unsqueeze(1), torch.tensor(y_val, dtype=torch.long))
    test_dataset = TensorDataset(torch.tensor(X_test, dtype=torch.float32).unsqueeze(1), torch.tensor(y_test, dtype=torch.long))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # 6. Initialize Model, Criterion, Optimizer
    device = torch.device("cpu")
    model = SentinelNet1DCNN(num_features=num_features, num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights_tensor.to(device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    best_val_loss = float("inf")
    best_weights = None

    logger.info("Starting neural network training loop...")
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        correct_train = 0
        total_train = 0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * batch_x.size(0)
            preds = outputs.argmax(dim=1)
            correct_train += (preds == batch_y).sum().item()
            total_train += batch_y.size(0)

        epoch_train_loss = train_loss / total_train
        epoch_train_acc = correct_train / total_train

        # Validation
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item() * batch_x.size(0)
                preds = outputs.argmax(dim=1)
                correct_val += (preds == batch_y).sum().item()
                total_val += batch_y.size(0)

        epoch_val_loss = val_loss / total_val
        epoch_val_acc = correct_val / total_val
        scheduler.step(epoch_val_loss)

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_weights = model.state_dict().copy()

        logger.info(
            f"Epoch [{epoch:02d}/{epochs:02d}] "
            f"Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc * 100:.2f}% | "
            f"Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc * 100:.2f}%"
        )

    # 7. Save Best Checkpoint
    model.load_state_dict(best_weights)
    torch.save({
        "model_state_dict": model.state_dict(),
        "num_features": num_features,
        "num_classes": num_classes,
        "classes": list(preprocessor.label_encoder.classes_),
        "feature_names": FEATURE_COLUMNS,
    }, model_save_path)
    logger.info(f"Saved optimized deep learning model checkpoint to: {model_save_path}")

    # 8. Evaluate on Held-Out Test Set
    from ml.evaluate import evaluate_test_set
    metrics = evaluate_test_set(model, test_loader, preprocessor, device, metrics_save_path)
    return model, preprocessor, metrics


if __name__ == "__main__":
    train_model()
