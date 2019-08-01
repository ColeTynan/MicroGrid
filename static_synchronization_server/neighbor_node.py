class NeighborNode:
    timestamp = -1
    processed_bool = False
    updated_timestamp_bool = False
    socket = 0
    disconnected = False

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port