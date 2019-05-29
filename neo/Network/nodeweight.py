from datetime import datetime


class NodeWeight:
    SPEED_RECORD_COUNT = 3
    SPEED_INIT_VALUE = 100 * 1024 ^ 2  # Start with a big speed of 100 MB/s

    REQUEST_TIME_RECORD_COUNT = 3

    def __init__(self, nodeid):
        self.id: int = nodeid
        self.speed = [self.SPEED_INIT_VALUE] * self.SPEED_RECORD_COUNT
        self.timeout_count = 0
        self.error_response_count = 0
        now = datetime.utcnow().timestamp() * 1000  # milliseconds
        self.request_time = [now] * self.REQUEST_TIME_RECORD_COUNT

    def append_new_speed(self, speed) -> None:
        # remove oldest
        self.speed.pop(-1)
        # add new
        self.speed.insert(0, speed)

    def append_new_request_time(self) -> None:
        self.request_time.pop(-1)

        now = datetime.utcnow().timestamp() * 1000  # milliseconds
        self.request_time.insert(0, now)

    def _avg_speed(self) -> float:
        return sum(self.speed) / self.SPEED_RECORD_COUNT

    def _avg_request_time(self) -> float:
        avg_request_time = 0
        now = datetime.utcnow().timestamp() * 1000  # milliseconds

        for t in self.request_time:
            avg_request_time += now - t

        avg_request_time = avg_request_time / self.REQUEST_TIME_RECORD_COUNT
        return avg_request_time

    def weight(self):
        # nodes with the highest speed and the longest time between querying for data have the highest weight
        # and will be accessed first unless their error/timeout count is higher. This distributes load across nodes
        weight = self._avg_speed() + self._avg_request_time()

        # punish errors and timeouts harder than slower speeds and more recent access
        if self.error_response_count:
            weight /= self.error_response_count + 1  # make sure we at least always divide by 2

        if self.timeout_count:
            weight /= self.timeout_count + 1
        return weight

    def __lt__(self, other):
        return self.weight() < other.weight()

    def __repr__(self):
        # return f"<{self.__class__.__name__} at {hex(id(self))}> w:{self.weight():.2f} r:{self.error_response_count} t:{self.timeout_count}"
        return f"{self.id} {self._avg_speed():.2f} {self._avg_request_time():.2f} w:{self.weight():.2f} r:{self.error_response_count} t:{self.timeout_count}"
