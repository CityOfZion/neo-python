from datetime import datetime


class FlightInfo:
    def __init__(self, node_id, height):
        self.node_id: int = node_id
        self.height: int = height
        self.start_time: int = datetime.utcnow().timestamp()

    def reset_start_time(self):
        self.start_time = datetime.utcnow().timestamp()
