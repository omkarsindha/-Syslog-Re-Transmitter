import random
import threading
import time
import socket
import pcaplib
import utils


class ReTransmitPacketsThread(threading.Thread):
    def __init__(self, file, is_remap, trg_ip, trg_port, protocol, ip, port, add_source, index, rate, loss):
        """Sends packets to new ip and port"""
        super().__init__()
        self.file: str = file
        self.is_remap = is_remap
        self.trg_ip: str = trg_ip  # Destination IP on packet
        self.trg_port: str = trg_port  # Destination Port on packet
        self.protocol = protocol
        self.ip = ip  # New IP to send the packet
        self.port = port  # New Port to send the packet
        self.add_source = add_source
        self.index = index
        self.loss = loss
        self.sent_count = self.index - 1  # Packet sent count
        self.total_packets = 0  # We do not know total packets
        self.packet_count_thread = PacketCountThread(file, is_remap, trg_ip, trg_port, protocol)
        self.end_event = threading.Event()
        self.playing_event = threading.Event()
        self.playing_event.set()

        # Adjust this to make the burst smoother
        self.bursts_per_second = 4
        self.rate = rate

        self.start()

    def run(self):
        """This is the method sends packets"""
        index_counter = 1  # self.index is 1 based index
        since_last_delay = 0

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            if utils.is_multicast(self.ip):
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            start_time = time.perf_counter()
            prev_delayed_packet_time = 0
            cap = pcaplib.CapFile(filename=self.file)
            for packet in cap:
                self.playing_event.wait()
                if not isinstance(packet, pcaplib.Packet):
                    continue
                if self.end_event.is_set():
                    break

                if self.protocol == 'UDP':
                    if not packet.udp_len:
                        continue
                elif self.protocol == 'TCP':
                    if packet.udp_len:
                        continue

                if self.is_remap:
                    pkt_trg_ip = socket.inet_ntoa(packet.dst)
                    pkt_trg_port = packet.dst_port
                    if (self.trg_ip != pkt_trg_ip) or (self.trg_port != pkt_trg_port):
                        continue

                if index_counter < self.index:
                    index_counter += 1
                    continue

                if self.add_source:
                    source_ip = socket.inet_ntoa(packet.src).encode('ascii')
                    payload = b'::%s::%s' % (source_ip, packet.get_payload())
                else:
                    payload = packet.get_payload()

                if self.rate == -1:   # Send packets realtime
                    if prev_delayed_packet_time == 0:         # Only for the first packet
                        prev_delayed_packet_time = packet.timestamp
                    elapsed = time.perf_counter() - start_time
                    delay = packet.timestamp - prev_delayed_packet_time - elapsed
                    if delay  >= 0.2:
                        time.sleep(delay)
                        prev_delayed_packet_time = packet.timestamp
                        start_time = time.perf_counter()
                else:          # Custom packet send rate by user
                    since_last_delay += 1
                    if since_last_delay > (self.rate / self.bursts_per_second):
                        elapsed = time.perf_counter() - start_time
                        sleep_time = (1 / self.bursts_per_second) - elapsed
                        if sleep_time >= 0:
                            time.sleep(sleep_time)
                        since_last_delay = 0
                        start_time = time.perf_counter()

                try:
                    rand_num = random.randint(1, 100)
                    if rand_num > self.loss:
                        sock.sendto(payload, (self.ip, self.port))
                    self.sent_count += 1
                except Exception as e:
                    print(f"Error sending message: {e}")

                if self.packet_count_thread is not None:
                    if self.packet_count_thread.end_event.is_set():
                        self.total_packets = self.packet_count_thread.total_packets
                        self.packet_count_thread = None
            cap.close()
        self.end_event.set()
# end class ReTransmitPacketsThread(threading.Thread)


class PacketCountThread(threading.Thread):
    def __init__(self, file, is_remap, trg_ip, trg_port, protocol):
        super().__init__()
        self.file: str = file
        self.is_remap = is_remap
        self.trg_ip: str = trg_ip  # Destination IP on packet
        self.trg_port: str = trg_port  # Destination Port on packet
        self.protocol = protocol
        self.total_packets = 0  # Packet count
        self.end_event = threading.Event()
        self.start()

    def run(self):
        """This is the method scans total packets"""
        cap = pcaplib.CapFile(filename=self.file)
        for packet in cap:
            if not isinstance(packet, pcaplib.Packet):
                continue
            if self.end_event.is_set():
                break
            if self.protocol == 'UDP':
                if not packet.udp_len:
                    continue
            elif self.protocol == 'TCP':
                if packet.udp_len:
                    continue

            if self.is_remap:
                pkt_trg_ip = socket.inet_ntoa(packet.dst)
                pkt_trg_port = packet.dst_port
                if (self.trg_ip != pkt_trg_ip) or (self.trg_port != pkt_trg_port):
                    continue

            self.total_packets += 1
        cap.close()
        self.end_event.set()
# end class PacketCountThread(threading.Thread):
