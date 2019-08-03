class NeighborNode:
    timestamp = -1
    timestamp_vals = {}
    timestamp_vals[0] = -1
    timestamp_vals[1] = -1
    processed_bool = False
    processed_signal = 1
    updated_timestamp_bool = False
    socket = 0
    disconnected = False

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port