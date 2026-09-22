"""
SentinelNet AI - Deep Learning Model Architectures
Implements 1D-CNN and Dense neural architectures for network flow intrusion detection.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SentinelNet1DCNN(nn.Module):
    """
    1D-Convolutional Deep Neural Network for flow classification.
    Captures localized multi-feature correlation patterns across statistical flow features.
    """
    def __init__(self, num_features: int = 22, num_classes: int = 5):
        super().__init__()
        self.num_features = num_features
        self.num_classes = num_classes

        # Convolutional Feature Extraction Block
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        
        self.conv2 = nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        
        self.pool1 = nn.MaxPool1d(kernel_size=2)
        self.drop1 = nn.Dropout(0.2)

        self.conv3 = nn.Conv1d(in_channels=128, out_channels=128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(128)

        self.global_pool = nn.AdaptiveAvgPool1d(1)

        # Classification Head
        self.fc1 = nn.Linear(128, 64)
        self.drop2 = nn.Dropout(0.3)
        self.fc2 = nn.Linear(64, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Input shape: (batch_size, num_features, 1) or (batch_size, 1, num_features)
        """
        # Ensure shape is (batch_size, 1, num_features) for Conv1d
        if x.dim() == 2:
            x = x.unsqueeze(1)
        elif x.dim() == 3 and x.shape[-1] == 1:
            x = x.permute(0, 2, 1)

        # Layer 1
        x = F.leaky_relu(self.bn1(self.conv1(x)), negative_slope=0.1)
        # Layer 2
        x = F.leaky_relu(self.bn2(self.conv2(x)), negative_slope=0.1)
        x = self.pool1(x)
        x = self.drop1(x)

        # Layer 3
        x = F.leaky_relu(self.bn3(self.conv3(x)), negative_slope=0.1)
        x = self.global_pool(x)  # (batch_size, 128, 1)
        x = x.squeeze(-1)        # (batch_size, 128)

        # Dense classification
        x = F.relu(self.fc1(x))
        x = self.drop2(x)
        logits = self.fc2(x)
        return logits

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Computes softmax probabilities across classes."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            return F.softmax(logits, dim=-1)


class SentinelNetMLP(nn.Module):
    """
    Multilayer Perceptron (MLP) baseline for architectural comparison.
    """
    def __init__(self, num_features: int = 22, num_classes: int = 5):
        super().__init__()
        self.fc1 = nn.Linear(num_features, 128)
        self.bn1 = nn.BatchNorm1d(128)
        self.fc2 = nn.Linear(128, 64)
        self.bn2 = nn.BatchNorm1d(64)
        self.fc3 = nn.Linear(64, 32)
        self.drop = nn.Dropout(0.3)
        self.out = nn.Linear(32, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            x = x.squeeze(-1)
        x = F.relu(self.bn1(self.fc1(x)))
        x = F.relu(self.bn2(self.fc2(x)))
        x = F.relu(self.fc3(x))
        x = self.drop(x)
        return self.out(x)
