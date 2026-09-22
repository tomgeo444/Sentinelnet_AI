"""
SentinelNet AI - Statistical Flow Feature Extractor
Extracts 22 streamable statistical features from bidirectional packet flow records.
"""

import math
import numpy as np

# Canonical feature ordering used across training, evaluation, and live inference
FEATURE_COLUMNS = [
    "flow_duration",
    "total_fwd_packets",
    "total_bwd_packets",
    "total_fwd_bytes",
    "total_bwd_bytes",
    "fwd_packet_length_mean",
    "fwd_packet_length_std",
    "bwd_packet_length_mean",
    "bwd_packet_length_std",
    "flow_packet_rate",
    "flow_byte_rate",
    "fwd_iat_mean",
    "fwd_iat_std",
    "bwd_iat_mean",
    "bwd_iat_std",
    "flow_iat_mean",
    "syn_flag_count",
    "fin_flag_count",
    "rst_flag_count",
    "psh_flag_count",
    "ack_flag_count",
    "protocol_num",
]


def calculate_mean_std(values: list[float]) -> tuple[float, float]:
    """Calculates sample mean and standard deviation safely."""
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    arr = np.array(values, dtype=np.float64)
    return float(np.mean(arr)), float(np.std(arr, ddof=1))


def calculate_iats(timestamps: list[float]) -> list[float]:
    """Calculates inter-arrival times between sequential packet timestamps."""
    if len(timestamps) < 2:
        return [0.0]
    sorted_ts = sorted(timestamps)
    return [max(0.0, sorted_ts[i] - sorted_ts[i - 1]) for i in range(1, len(sorted_ts))]


def extract_features_from_flow(flow_data: dict) -> dict:
    """
    Extracts numerical feature dictionary from a flow object.
    
    flow_data structure:
        - fwd_packet_lengths: list[int]
        - bwd_packet_lengths: list[int]
        - fwd_timestamps: list[float]
        - bwd_timestamps: list[float]
        - all_timestamps: list[float]
        - flags: dict (syn, fin, rst, psh, ack, urg)
        - protocol_num: int (e.g. 6 for TCP, 17 for UDP, 1 for ICMP)
        - start_time: float
        - last_time: float
    """
    start_time = flow_data.get("start_time", 0.0)
    last_time = flow_data.get("last_time", start_time)
    duration = max(0.0001, last_time - start_time)

    fwd_lens = flow_data.get("fwd_packet_lengths", [])
    bwd_lens = flow_data.get("bwd_packet_lengths", [])

    fwd_pkts = len(fwd_lens)
    bwd_pkts = len(bwd_lens)
    tot_pkts = fwd_pkts + bwd_pkts

    fwd_bytes = sum(fwd_lens)
    bwd_bytes = sum(bwd_lens)
    tot_bytes = fwd_bytes + bwd_bytes

    fwd_len_mean, fwd_len_std = calculate_mean_std(fwd_lens)
    bwd_len_mean, bwd_len_std = calculate_mean_std(bwd_lens)

    packet_rate = tot_pkts / duration
    byte_rate = tot_bytes / duration

    # Inter-arrival times
    fwd_iats = calculate_iats(flow_data.get("fwd_timestamps", []))
    bwd_iats = calculate_iats(flow_data.get("bwd_timestamps", []))
    all_iats = calculate_iats(flow_data.get("all_timestamps", []))

    fwd_iat_mean, fwd_iat_std = calculate_mean_std(fwd_iats)
    bwd_iat_mean, bwd_iat_std = calculate_mean_std(bwd_iats)
    flow_iat_mean, _ = calculate_mean_std(all_iats)

    flags = flow_data.get("flags", {})
    syn_count = flags.get("syn", 0)
    fin_count = flags.get("fin", 0)
    rst_count = flags.get("rst", 0)
    psh_count = flags.get("psh", 0)
    ack_count = flags.get("ack", 0)

    proto_num = flow_data.get("protocol_num", 6)

    features = {
        "flow_duration": round(duration, 6),
        "total_fwd_packets": fwd_pkts,
        "total_bwd_packets": bwd_pkts,
        "total_fwd_bytes": fwd_bytes,
        "total_bwd_bytes": bwd_bytes,
        "fwd_packet_length_mean": round(fwd_len_mean, 4),
        "fwd_packet_length_std": round(fwd_len_std, 4),
        "bwd_packet_length_mean": round(bwd_len_mean, 4),
        "bwd_packet_length_std": round(bwd_len_std, 4),
        "flow_packet_rate": round(packet_rate, 4),
        "flow_byte_rate": round(byte_rate, 4),
        "fwd_iat_mean": round(fwd_iat_mean, 6),
        "fwd_iat_std": round(fwd_iat_std, 6),
        "bwd_iat_mean": round(bwd_iat_mean, 6),
        "bwd_iat_std": round(bwd_iat_std, 6),
        "flow_iat_mean": round(flow_iat_mean, 6),
        "syn_flag_count": syn_count,
        "fin_flag_count": fin_count,
        "rst_flag_count": rst_count,
        "psh_flag_count": psh_count,
        "ack_flag_count": ack_count,
        "protocol_num": proto_num,
    }

    # Validate finite values
    for k, v in features.items():
        if math.isnan(v) or math.isinf(v):
            features[k] = 0.0

    return features


def feature_dict_to_vector(feat_dict: dict) -> np.ndarray:
    """Converts a feature dictionary into a 1D NumPy array according to FEATURE_COLUMNS order."""
    return np.array([float(feat_dict.get(col, 0.0)) for col in FEATURE_COLUMNS], dtype=np.float32)
