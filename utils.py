def is_valid_port(port_str):
    """
    Simple port validation.
    Returns: bool
    """
    try:
        port = int(port_str)
        return 1 <= port <= 65535
    except ValueError:
        return False


def is_valid_ip(ip_str):
    """
    Simple IPv4 address validation.
    Returns: bool
    """
    parts = ip_str.split('.')
    if len(parts) == 4 and all(part.isdigit() and 0 <= int(part) < 256 for part in parts):
        return True
    return False

def to_string(input, encoding='utf-8', errors='replace'):
    """Convert PacketPayload to String"""
    if isinstance(input, str):
        return input
    elif isinstance(input, bytes):
        return input.decode(encoding, errors)
    else:
        return ""