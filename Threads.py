import threading
import time
import socket
import pcaplib


class ReTransmitPacketsThread(threading.Thread):
    def __init__(self, file, trg_ip, trg_port, protocol, ip, port, add_source, index, delay):
        """Sends packets to new ip and port"""
        super().__init__()
        self.file: str = file
        self.trg_ip: str = trg_ip          # Destination IP on packet
        self.trg_port: str = trg_port      # Destination Port on packet
        self.protocol = protocol
        self.ip = ip        # New IP to send the packet
        self.port = port    # New Port to send the packet
        self.add_source = add_source
        self.index = index
        self.delay = 1 / delay

        # Updated while thread is running for each packet sent.
        self.count = 0    # Packet sent count
        self.end_event = threading.Event()
        self.start()

    def run(self):
        """This is the method sends packets"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        cap = pcaplib.CapFile(filename=self.file)

        index_counter = 1    # self.index is 1 based index
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
            try:
                sock.sendto(payload, (self.ip, self.port))
                self.count += 1
                print("Forwarded the Packet...")
                time.sleep(self.delay)
            except Exception as e:
                print(f"Error sending message: {e}")

        sock.close()
        self.end_event.set()
# end class ReTransmitPacketsThread(threading.Thread)
