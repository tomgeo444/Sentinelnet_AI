# SentinelNet AI 🛡️
### Real-Time AI Network Intrusion Detection & Security Operations Monitoring System

**SentinelNet AI** is a complete, production-grade Deep Learning Network Intrusion Detection System (NIDS). Built for live cybersecurity monitoring, SentinelNet AI captures live packet streams, aggregates raw bidirectional flows, extracts 22 streamable statistical features, executes low-latency 1D-Convolutional Neural Network (1D-CNN) inference, assesses threat risk, records detections into MariaDB/MySQL (with zero-config SQLite fallback), and visualizes security events in real-time across an interactive SOC dashboard via WebSockets.

---

## 1. System Architecture

```
               [ LIVE NETWORK TRAFFIC ]
                (Local Interface / lo / wlan0 / eth0)
                          │
                          ▼
            [ SCAPY PACKET CAPTURE ENGINE ]
            (Async worker thread, port filter)
                          │
                          ▼
        [ BIDIRECTIONAL FLOW AGGREGATOR ]
        (5-Tuple: src_ip, dst_ip, sport, dport, proto)
        (Sliding window & Active/Idle timeout manager)
                          │
                          ▼
        [ 22-FEATURE STATISTICAL EXTRACTOR ]
        (Packet lengths, IAT, flow rates, TCP flags)
                          │
                          ▼
         [ PREPROCESSING & SCALING PIPELINE ]
         (StandardScaler + Multi-Class LabelEncoder)
                          │
                          ▼
         [ DEEP LEARNING 1D-CNN CLASSIFIER ]
         (1D Conv + BatchNorm + Dense Residual Head)
                          │
                          ▼
             [ RULE-BASED RISK ENGINE ]
        (NORMAL / LOW / MEDIUM / HIGH / CRITICAL)
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    [ DATABASE PERSISTENCE ]     [ WEBSOCKET BROADCASTER ]
    (MariaDB / MySQL / SQLite)   (FastAPI Async Event Loop)
                                        │
                                        ▼
                            [ SOC BROWSER DASHBOARD ]
                            (Chart.js, Live Tables, Alerts)
```

---

## 2. Feature Engineering & Live Traffic Parity

### Canonical 5-Tuple Definition
Each bidirectional flow is uniquely identified by:
$$\text{FlowKey} = \big(\min(\text{IP}_{\text{src}}, \text{IP}_{\text{dst}}), \max(\text{IP}_{\text{src}}, \text{IP}_{\text{dst}}), \text{Port}_{\text{src}}, \text{Port}_{\text{dst}}, \text{Protocol}\big)$$

### 22 Streamable Flow Features
To eliminate training-serving domain gap, SentinelNet AI uses only features that can be mathematically computed on live sliding flow windows without requiring retrospective session knowledge:

| # | Feature Name | Description | Formula / Source |
|---|---|---|---|
| 1 | `flow_duration` | Total duration of flow in seconds | $T_{\text{last}} - T_{\text{start}}$ |
| 2 | `total_fwd_packets` | Packets in forward direction | $N_{\text{fwd}}$ |
| 3 | `total_bwd_packets` | Packets in backward direction | $N_{\text{bwd}}$ |
| 4 | `total_fwd_bytes` | Payload/header bytes in forward direction | $\sum L_{\text{fwd}}$ |
| 5 | `total_bwd_bytes` | Payload/header bytes in backward direction | $\sum L_{\text{bwd}}$ |
| 6 | `fwd_packet_length_mean` | Mean length of forward packets | $\mu(L_{\text{fwd}})$ |
| 7 | `fwd_packet_length_std` | Standard deviation of forward packet lengths | $\sigma(L_{\text{fwd}})$ |
| 8 | `bwd_packet_length_mean` | Mean length of backward packets | $\mu(L_{\text{bwd}})$ |
| 9 | `bwd_packet_length_std` | Standard deviation of backward packet lengths | $\sigma(L_{\text{bwd}})$ |
| 10 | `flow_packet_rate` | Packet throughput per second | $(N_{\text{fwd}} + N_{\text{bwd}}) / \Delta t$ |
| 11 | `flow_byte_rate` | Byte throughput per second | $(\sum L_{\text{fwd}} + \sum L_{\text{bwd}}) / \Delta t$ |
| 12 | `fwd_iat_mean` | Forward packet inter-arrival time mean | $\mu(\Delta t_{\text{fwd}})$ |
| 13 | `fwd_iat_std` | Forward packet inter-arrival time standard deviation | $\sigma(\Delta t_{\text{fwd}})$ |
| 14 | `bwd_iat_mean` | Backward packet inter-arrival time mean | $\mu(\Delta t_{\text{bwd}})$ |
| 15 | `bwd_iat_std` | Backward packet inter-arrival time standard deviation | $\sigma(\Delta t_{\text{bwd}})$ |
| 16 | `flow_iat_mean` | Inter-arrival time mean across all packets | $\mu(\Delta t_{\text{all}})$ |
| 17 | `syn_flag_count` | Number of TCP packets with SYN flag set | $\sum \mathbb{I}(\text{SYN})$ |
| 18 | `fin_flag_count` | Number of TCP packets with FIN flag set | $\sum \mathbb{I}(\text{FIN})$ |
| 19 | `rst_flag_count` | Number of TCP packets with RST flag set | $\sum \mathbb{I}(\text{RST})$ |
| 20 | `psh_flag_count` | Number of TCP packets with PSH flag set | $\sum \mathbb{I}(\text{PSH})$ |
| 21 | `ack_flag_count` | Number of TCP packets with ACK flag set | $\sum \mathbb{I}(\text{ACK})$ |
| 22 | `protocol_num` | Numerical IP protocol number (6=TCP, 17=UDP, 1=ICMP) | $\text{Proto}_{\text{IP}}$ |

---

## 3. Deep Learning Model Architecture

SentinelNet AI utilizes a **1D-Convolutional Neural Network (1D-CNN)** with batch normalization and residual dense classification heads.

### Technical Justification for 1D-CNN:
Unlike standard tabular classifiers, network flow features possess strong local structural correlations (e.g., the co-occurrence of zero backward packets, high SYN flag ratios, and tiny inter-arrival times during a port scan). A 1D-CNN applies convolutional kernels across adjacent statistical feature dimensions, learning spatial feature representations invariant to individual scale fluctuations.

```
Input: Tensor of shape [Batch, 1, 22]
  │
  ├── 1D Convolution (Filters: 64, Kernel: 3, Padding: Same)
  ├── Batch Normalization + LeakyReLU (alpha=0.1)
  │
  ├── 1D Convolution (Filters: 128, Kernel: 3, Padding: Same)
  ├── Batch Normalization + LeakyReLU (alpha=0.1)
  ├── 1D Max Pooling (Pool Size: 2) + Dropout (p=0.2)
  │
  ├── 1D Convolution (Filters: 128, Kernel: 3, Padding: Same)
  ├── Batch Normalization + LeakyReLU (alpha=0.1)
  ├── Adaptive Average Pooling 1D (Output size: 1)
  │
  ├── Flatten -> Dense (128 units) + ReLU + Dropout (p=0.3)
  ├── Dense (64 units) + ReLU + Dropout (p=0.2)
  └── Dense Output (5 units) + Softmax -> [P(BENIGN), P(DoS), P(PortScan), P(BruteForce), P(Bot)]
```

---

## 4. Transparent Risk Classification Engine

The system maps model predictions and confidence into five operational SOC triage levels:

- **NORMAL**: Predicted `BENIGN` with confidence $\ge 0.60$.
- **LOW**: Predicted `BENIGN` with uncertainty ($<0.60$) or low-confidence scan probes.
- **MEDIUM**: Confirmed `PortScan` ($\ge 0.70$ confidence) or moderate brute force activity.
- **HIGH**: Confirmed `BruteForce` auth attempts or elevated DoS bursts.
- **CRITICAL**: High-confidence `DoS_DDoS` floods ($\ge 0.80$ confidence) or active `Bot_Infiltration` command-and-control beacons.

---

## 5. Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, WebSockets, Pydantic
- **Deep Learning & ML**: PyTorch (1D-CNN), Scikit-Learn, NumPy, Pandas, Joblib
- **Packet & Flow Processing**: Scapy, Psutil
- **Database**: MariaDB / MySQL (Production) with automatic SQLite fallback (Dev/Demo)
- **Frontend SOC Dashboard**: HTML5, CSS3 (Cyber SOC Dark Theme), Vanilla JavaScript, Chart.js, FontAwesome

---

## 6. Installation & Fedora Linux Setup

### Step 1: Install System Packages (Fedora)
```bash
sudo dnf install -y python3.12 python3-pip mariadb-server tcpdump libpcap-devel
```

### Step 2: Configure Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Optional MariaDB Setup (or rely on SQLite fallback)
```bash
# Start MariaDB service
sudo systemctl enable --now mariadb

# Create Database and User
sudo mariadb -u root -e "
CREATE DATABASE IF NOT EXISTS sentinelnet_db;
CREATE USER IF NOT EXISTS 'sentinel'@'localhost' IDENTIFIED BY 'sentinel_secure_pass';
GRANT ALL PRIVILEGES ON sentinelnet_db.* TO 'sentinel'@'localhost';
FLUSH PRIVILEGES;
"
```

### Step 4: Network Capture Permissions
To allow non-root packet sniffing with Scapy:
```bash
sudo setcap cap_net_raw,cap_net_admin=eip $(readlink -f $(which python3.12))
```

---

## 7. Model Training & Evaluation

To train the 1D-CNN classifier and generate academic evaluation metrics:
```bash
source venv/bin/activate
python -m ml.train
```

Outputs generated:
- Model checkpoint: `models/sentinelnet_model.pt`
- Normalizer & Encoders: `models/scaler.joblib`, `models/label_encoder.joblib`, `models/feature_names.json`
- Academic metrics report: `models/model_metrics.json`
- Confusion matrix plot: `models/confusion_matrix.png`

---

## 8. Running SentinelNet AI

### Start the Application Server:
```bash
source venv/bin/activate
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
**`http://127.0.0.1:8000/`**

---

## 9. 5–10 Minute Live Demonstration Guide

Follow this step-by-step procedure during an exam or teacher demonstration:

1. **Start SentinelNet AI**: Launch the backend server with `uvicorn backend.main:app --host 127.0.0.1 --port 8000`.
2. **Open Dashboard**: Navigate to `http://127.0.0.1:8000/`.
3. **Verify Status**: Confirm the top status bar displays `Backend: ONLINE`, `Database: CONNECTED (MariaDB/SQLite)`, `Model: 1D-CNN LOADED`, and `Interface: lo`.
4. **Click [ START MONITORING ]**: The monitoring badge toggles to green `ACTIVE`, initializing live packet sniffing.
5. **Generate Normal Traffic**: Click the **"Normal Traffic"** demo button (or run `python demo/demo_traffic.py --mode normal`).
   - Observe live packet and flow counters incrementing.
   - Observe green normal flow records populating the Live Detections Table.
6. **Generate a Simulated Port Scan**: Click the **"Port Scan"** demo button (or run `python demo/demo_traffic.py --mode portscan`).
   - Observe the 1D-CNN instantly classifying the rapid SYN sweep as `PortScan`.
   - Observe the real-time **Alert Banner** pulsing in amber with high confidence (>95%).
7. **Generate a Simulated DoS Flood**: Click the **"SYN Flood (DoS)"** demo button (or run `python demo/demo_traffic.py --mode synflood`).
   - Observe the throughput spike in the Throughput Time Series chart.
   - Observe the red `CRITICAL RISK` alert banner for `DoS_DDoS`.
8. **Inspect Persistent Storage**: Open the database or check `/api/detections` to show records stored in MariaDB/SQLite.
9. **Review Model Performance**: Scroll down to the Model Architecture card to showcase the real test set Accuracy, Precision, Recall, and F1-score.

---

## 10. Teacher Defense & Academic Q&A

### Q1: What problem does SentinelNet AI solve?
*Answer:* Modern corporate and cloud networks face stealthy reconnaissance and distributed denial-of-service attacks. Traditional signature-based NIDS (like Snort/Suricata rules) fail against novel attacks and encrypted/evasive traffic. SentinelNet AI solves this by classifying bidirectional statistical flow dynamics using Deep Learning.

### Q2: Why use Deep Learning (1D-CNN) instead of simple Decision Trees or Random Forests?
*Answer:* Flow features have spatial and cross-dimensional correlations (such as the ratio of forward-to-backward packets relative to inter-arrival jitter and flag distributions). A 1D-CNN automatically learns non-linear hierarchical representations across these feature channels without manual heuristic rule engineering.

### Q3: How do you bridge the Domain Gap between offline datasets and live network traffic?
*Answer:* Many academic datasets (like full CICIDS2017) include over 80 features, some of which require complete retrospective knowledge of long-terminated sessions. SentinelNet AI resolves this by engineering a streamable 22-feature statistical vector that is computed over real-time sliding flow windows. Both the training dataset and the live Scapy flow aggregator use the exact same mathematical definitions.

### Q4: How does the system handle class imbalance?
*Answer:* In real networks, benign traffic vastly outweighs attack traffic. SentinelNet AI balances cross-entropy loss during training using inverse class frequency weights ($w_c = \frac{N}{K \cdot N_c}$), ensuring minority attack classes (like Botnet infiltration and Brute Force) achieve high recall without being overwhelmed by Benign traffic.

---

## 11. Automated Test Suite

To run all unit, integration, and end-to-end tests:
```bash
pytest tests/ -v
```

All 7 test suites verify:
- Feature extraction mathematical accuracy
- Preprocessing transformation & serialization
- Deep learning neural network forward pass & tensor shapes
- Database CRUD & connection failover
- REST API endpoints
- WebSocket streaming and event dispatch
- Full end-to-end packet-to-database detection pipeline
