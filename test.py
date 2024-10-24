import pcaplib 
import socket
import time


cap = pcaplib.CapFile(filename="C:\\Users\\osindha\\Downloads\\capture.pcapng")
syslog_packets = []

for packet in cap:
    if not isinstance(packet, pcaplib.Packet):
        continue

    if packet.udp_len is None:     # Not a UDP Packet
        continue

    if packet.dst_port != 514:    # Not a Syslog Packet
        continue

    syslog_packets.append(packet)

print("Read {:,} syslog packets".format(len(syslog_packets)))

IP = '127.0.0.1' # Loopback
PORT = 514

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for packet in syslog_packets:
    try:
        # Send the message
        sock.sendto(packet.get_payload(), (IP, PORT))
        time.sleep(1)
        print(f"Message sent to {IP}:{PORT}")
    except Exception as e:
        print(f"Error sending message: {e}")

sock.close()
