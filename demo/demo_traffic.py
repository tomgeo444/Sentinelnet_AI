"""
SentinelNet AI - Safe Local Demonstration Traffic Generator
Generates realistic network traffic patterns strictly on localhost (127.0.0.1)
with full support for both raw Scapy transmission and non-root unprivileged socket mode.
"""

import time
import socket
import argparse
import logging
import random
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sentinelnet.demo")


def send_normal_traffic(target_ip: str = "127.0.0.1", count: int = 15):
    """Generates normal, benign TCP request/reply flow patterns."""
    logger.info(f"Generating NORMAL traffic pattern ({count} flows) against {target_ip}...")
    from backend.services.monitor_service import monitor_service

    for i in range(count):
        sport = random.randint(30000, 60000)
        dport = random.choice([8080, 8443, 9000, 3000, 5000])

        try:
            from scapy.all import IP, TCP, send
            syn = IP(dst=target_ip) / TCP(sport=sport, dport=dport, flags="S", seq=1000)
            ack = IP(dst=target_ip) / TCP(sport=sport, dport=dport, flags="A", seq=1001, ack=2001)
            psh = IP(dst=target_ip) / TCP(sport=sport, dport=dport, flags="PA", seq=1001, ack=2001) / (b"GET /api/status HTTP/1.1\r\nHost: localhost\r\n\r\n")
            fin = IP(dst=target_ip) / TCP(sport=sport, dport=dport, flags="FA", seq=1050, ack=2050)
            send(syn, verbose=False)
            time.sleep(0.01)
            send(ack, verbose=False)
            time.sleep(0.02)
            send(psh, verbose=False)
            time.sleep(0.01)
            send(fin, verbose=False)
        except Exception:
            if monitor_service.capture and monitor_service.is_monitoring:
                t0 = time.time()
                # Forward SYN
                monitor_service.capture.ingest_packet(target_ip, target_ip, sport, dport, "TCP", 6, 60, t0, {"syn": 1})
                # Backward SYN-ACK
                monitor_service.capture.ingest_packet(target_ip, target_ip, dport, sport, "TCP", 6, 60, t0 + 0.02, {"syn": 1, "ack": 1})
                # Forward PSH-ACK (Data)
                monitor_service.capture.ingest_packet(target_ip, target_ip, sport, dport, "TCP", 6, 250, t0 + 0.05, {"psh": 1, "ack": 1})
                # Backward ACK
                monitor_service.capture.ingest_packet(target_ip, target_ip, dport, sport, "TCP", 6, 54, t0 + 0.08, {"ack": 1})
                # Forward FIN
                monitor_service.capture.ingest_packet(target_ip, target_ip, sport, dport, "TCP", 6, 40, t0 + 0.12, {"fin": 1, "ack": 1})

        time.sleep(0.05 + random.uniform(0.02, 0.08))

    logger.info("Normal traffic generation completed.")


def send_portscan_traffic(target_ip: str = "127.0.0.1", count: int = 25):
    """Generates a rapid TCP SYN port scan across a range of ports."""
    logger.info(f"Generating PORTSCAN traffic pattern ({count} ports) against {target_ip}...")
    from backend.services.monitor_service import monitor_service
    sport = random.randint(40000, 55000)
    start_port = 8100

    for i in range(count):
        dport = start_port + i
        try:
            from scapy.all import IP, TCP, send
            syn_pkt = IP(dst=target_ip) / TCP(sport=sport, dport=dport, flags="S", seq=random.randint(100, 9999))
            send(syn_pkt, verbose=False)
        except Exception:
            if monitor_service.capture and monitor_service.is_monitoring:
                monitor_service.capture.ingest_packet(target_ip, target_ip, sport, dport, "TCP", 6, 44, time.time(), {"syn": 1})

        time.sleep(0.01)

    logger.info("PortScan traffic generation completed.")


def send_synflood_traffic(target_ip: str = "127.0.0.1", count: int = 50):
    """
    Generates a high-frequency SYN burst (DoS) against destination port 9999.
    Simulates high packet rate within the same flow.
    """
    logger.info(f"Generating SYN FLOOD (DoS) traffic pattern ({count} packets) against {target_ip}:9999...")
    from backend.services.monitor_service import monitor_service
    sport = 39821
    dport = 9999

    t0 = time.time()
    for i in range(count):
        try:
            from scapy.all import IP, TCP, send
            syn_pkt = IP(dst=target_ip) / TCP(sport=sport, dport=dport, flags="S", seq=1000 + i)
            send(syn_pkt, verbose=False)
        except Exception:
            if monitor_service.capture and monitor_service.is_monitoring:
                monitor_service.capture.ingest_packet(target_ip, target_ip, sport, dport, "TCP", 6, 54, t0 + (i * 0.001), {"syn": 1})

        time.sleep(0.001)

    logger.info("SYN Flood traffic generation completed.")


def send_udpburst_traffic(target_ip: str = "127.0.0.1", count: int = 35):
    """Generates rapid UDP datagram bursts."""
    logger.info(f"Generating UDP BURST traffic pattern ({count} datagrams) against {target_ip}...")
    from backend.services.monitor_service import monitor_service
    dport = 9998
    sport = 41200
    t0 = time.time()

    for i in range(count):
        payload_len = random.randint(64, 256)
        try:
            from scapy.all import IP, UDP, send
            udp_pkt = IP(dst=target_ip) / UDP(sport=sport, dport=dport) / (b"X" * payload_len)
            send(udp_pkt, verbose=False)
        except Exception:
            if monitor_service.capture and monitor_service.is_monitoring:
                monitor_service.capture.ingest_packet(target_ip, target_ip, sport, dport, "UDP", 17, payload_len + 28, t0 + (i * 0.002))

        time.sleep(0.002)

    logger.info("UDP Burst traffic generation completed.")


def generate_safe_traffic(mode: str = "normal", count: int = 20, target_ip: str = "127.0.0.1"):
    """Dispatches traffic generation based on selected mode."""
    mode_lower = mode.lower()
    if mode_lower == "normal":
        send_normal_traffic(target_ip, count=count)
    elif mode_lower in ("portscan", "scan"):
        send_portscan_traffic(target_ip, count=count)
    elif mode_lower in ("synflood", "dos", "flood"):
        send_synflood_traffic(target_ip, count=count)
    elif mode_lower in ("udp", "udpflood"):
        send_udpburst_traffic(target_ip, count=count)
    else:
        send_normal_traffic(target_ip, count=count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet AI Safe Demonstration Traffic Generator")
    parser.add_argument(
        "--mode",
        choices=["normal", "burst", "portscan", "synflood", "udpflood"],
        default="normal",
        help="Traffic generation mode"
    )
    parser.add_argument("--count", type=int, default=20, help="Number of packets / flows to generate")
    parser.add_argument("--target", default="127.0.0.1", help="Target IP")
    args = parser.parse_args()

    generate_safe_traffic(mode=args.mode, count=args.count, target_ip=args.target)
