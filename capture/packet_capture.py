"""
SentinelNet AI - Live Packet Capture Engine
Sniffs live network packets, handles Linux raw socket permissions gracefully,
filters feedback loops, and coordinates with the flow aggregation manager.
"""

import time
import socket
import logging
import threading
import psutil
from capture.flow_manager import FlowManager

logger = logging.getLogger("sentinelnet.capture")


def list_network_interfaces() -> list[dict]:
    """
    Discovers and enumerates all available network interfaces on the host.
    Returns interface details including names, IPv4 addresses, and active status.
    """
    interfaces = []
    try:
        from scapy.all import get_if_list
        scapy_ifs = set(get_if_list())
    except Exception:
        scapy_ifs = set()

    psutil_addrs = psutil.net_if_addrs()
    psutil_stats = psutil.net_if_stats()

    all_names = scapy_ifs.union(set(psutil_addrs.keys()))

    for iface_name in all_names:
        addrs = psutil_addrs.get(iface_name, [])
        ipv4 = "N/A"
        mac = "N/A"
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ipv4 = addr.address
            elif hasattr(psutil, "AF_LINK") and addr.family == psutil.AF_LINK:
                mac = addr.address

        stats = psutil_stats.get(iface_name)
        is_up = stats.isup if stats else True
        is_loopback = (iface_name == "lo" or ipv4.startswith("127."))

        interfaces.append({
            "name": iface_name,
            "ip": ipv4,
            "mac": mac,
            "is_up": is_up,
            "is_loopback": is_loopback,
        })

    # Sort so active non-loopback interfaces appear first, followed by loopback
    interfaces.sort(key=lambda x: (not x["is_up"], x["is_loopback"], x["name"]))
    return interfaces


def get_default_interface() -> str:
    """Selects the most suitable default network interface."""
    interfaces = list_network_interfaces()
    if not interfaces:
        return "lo"
    
    # Prefer loopback or UP interface with assigned IPv4
    for iface in interfaces:
        if iface["name"] == "lo":
            return "lo"

    for iface in interfaces:
        if iface["is_up"] and iface["ip"] != "N/A":
            return iface["name"]

    return interfaces[0]["name"]


class LivePacketCapture:
    """
    Asynchronous packet sniffer running in dedicated background worker threads.
    Feeds parsed packets directly to FlowManager and periodically flushes flows.
    """
    def __init__(
        self,
        interface: str = None,
        server_port_filter: int = 8000,
        flow_manager: FlowManager = None,
        on_packet_callback = None,
    ):
        self.interface = interface or get_default_interface()
        self.server_port_filter = server_port_filter
        self.flow_manager = flow_manager or FlowManager()
        self.on_packet_callback = on_packet_callback

        self._is_running = False
        self._thread: threading.Thread = None
        self._flush_thread: threading.Thread = None
        self._packet_count = 0
        self._byte_count = 0
        self._lock = threading.Lock()
        self.capture_mode = "RAW_SOCKET"
        self.permission_warning = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def packet_count(self) -> int:
        return self._packet_count

    @property
    def byte_count(self) -> int:
        return self._byte_count

    def ingest_packet(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol_name: str,
        protocol_num: int,
        length: int,
        timestamp: float = None,
        tcp_flags: dict = None,
    ):
        """Direct packet ingestion method (used by raw sniffer and user-space socket interceptor)."""
        if not self._is_running:
            return

        # Avoid self-monitoring loops on the SentinelNet server port
        if self.server_port_filter and (src_port == self.server_port_filter or dst_port == self.server_port_filter):
            return

        ts = timestamp if timestamp is not None else time.time()

        with self._lock:
            self._packet_count += 1
            self._byte_count += length

        # Pass to flow aggregation manager
        self.flow_manager.process_packet(
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol_name=protocol_name,
            protocol_num=protocol_num,
            length=length,
            timestamp=ts,
            tcp_flags=tcp_flags,
        )

        if self.on_packet_callback:
            try:
                self.on_packet_callback({
                    "timestamp": ts,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": protocol_name,
                    "length": length,
                })
            except Exception as e:
                logger.debug(f"Error in on_packet_callback: {e}")

    def _parse_tcp_flags(self, tcp_pkt) -> dict:
        """Extracts individual TCP control flags."""
        flags = int(tcp_pkt.flags)
        return {
            "syn": 1 if (flags & 0x02) else 0,
            "fin": 1 if (flags & 0x01) else 0,
            "rst": 1 if (flags & 0x04) else 0,
            "psh": 1 if (flags & 0x08) else 0,
            "ack": 1 if (flags & 0x10) else 0,
            "urg": 1 if (flags & 0x20) else 0,
        }

    def _scapy_packet_handler(self, packet):
        """Processes each captured raw Scapy packet."""
        from scapy.all import IP, IPv6, TCP, UDP, ICMP

        ts = float(packet.time) if hasattr(packet, "time") else time.time()
        length = len(packet)

        src_ip = None
        dst_ip = None
        proto_name = "OTHER"
        proto_num = 0
        src_port = 0
        dst_port = 0
        tcp_flags = None

        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            proto_num = packet[IP].proto
        elif IPv6 in packet:
            src_ip = packet[IPv6].src
            dst_ip = packet[IPv6].dst
            proto_num = packet[IPv6].nh
        else:
            return

        if TCP in packet:
            proto_name = "TCP"
            src_port = int(packet[TCP].sport)
            dst_port = int(packet[TCP].dport)
            tcp_flags = self._parse_tcp_flags(packet[TCP])
        elif UDP in packet:
            proto_name = "UDP"
            src_port = int(packet[UDP].sport)
            dst_port = int(packet[UDP].dport)
        elif ICMP in packet:
            proto_name = "ICMP"
            src_port = 0
            dst_port = 0

        self.ingest_packet(
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol_name=proto_name,
            protocol_num=proto_num,
            length=length,
            timestamp=ts,
            tcp_flags=tcp_flags,
        )

    def _flush_loop(self):
        """Periodically flushes idle and expired flows."""
        while self._is_running:
            time.sleep(0.5)
            if self._is_running:
                self.flow_manager.flush_expired_flows()

    def _sniff_worker(self):
        """Worker loop executing Scapy sniff with automatic unprivileged fallback."""
        logger.info(f"Starting Scapy packet capture on interface: '{self.interface}'")
        try:
            from scapy.all import sniff
            sniff(
                iface=self.interface,
                prn=self._scapy_packet_handler,
                stop_filter=lambda p: not self._is_running,
                store=False,
            )
        except PermissionError as pe:
            self.capture_mode = "USER_SPACE_FALLBACK"
            self.permission_warning = (
                "Raw packet sniffing requires CAP_NET_RAW or sudo. "
                "Active in User-Space Socket Tap Mode (live demo traffic active)."
            )
            logger.warning(f"Raw socket permission denied: {pe}. Running in User-Space Socket Tap Mode.")
        except Exception as e:
            logger.error(f"Scapy sniffing terminated with error: {e}")

    def start(self):
        """Starts live packet capture in background threads."""
        if self._is_running:
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._sniff_worker, daemon=True, name="SnifferThread")
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True, name="FlowFlushThread")

        self._thread.start()
        self._flush_thread.start()
        logger.info("Live packet capture worker threads started.")

    def stop(self):
        """Stops packet capture and flushes all remaining flows."""
        if not self._is_running:
            return

        logger.info("Stopping packet capture...")
        self._is_running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=0.5)

        # Flush any remaining flows
        self.flow_manager.flush_expired_flows(current_time=time.time() + 100.0)
        logger.info(f"Packet capture stopped. Total packets: {self._packet_count}, Total bytes: {self._byte_count}")
