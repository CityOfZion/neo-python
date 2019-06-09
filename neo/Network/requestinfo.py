from neo.Network.flightinfo import FlightInfo


class RequestInfo:
    def __init__(self, height):
        self.height: int = height
        self.failed_nodes: dict = dict()  # nodeId: timeout time
        self.failed_total: int = 0
        self.flights: dict = dict()  # nodeId:FlightInfo
        self.last_used_node = None

    def add_new_flight(self, flight_info: FlightInfo) -> None:
        self.flights[flight_info.node_id] = flight_info
        self.last_used_node = flight_info.node_id

    def most_recent_flight(self) -> FlightInfo:
        return self.flights[self.last_used_node]

    def mark_failed_node(self, node_id) -> None:
        self.failed_nodes[node_id] = self.failed_nodes.get(node_id, 0) + 1
        self.failed_total += 1
