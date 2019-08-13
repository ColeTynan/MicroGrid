class NeighborNode:
    timestamp = -1
    timestamp_vals = dict()
    processed_bool = False
    processed_signal = 1
    updated_timestamp_bool = False
    socket = 0
    sent_data = False
    disconnected = False

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port