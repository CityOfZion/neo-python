import datetime


class Address:
    def __init__(self, address: str, last_connection_to: float = None):
        """
        Initialize
        Args:
            address: a host:port 
            last_connection_to: timestamp since we were last connected. Default's to 0 indicating 'never'
        """
        if not last_connection_to:
            self.last_connection = 0
        else:
            self.last_connection = last_connection_to

        self.address = address  # type: str

    @classmethod
    def Now(cls):
        return datetime.datetime.utcnow().timestamp()

    def __eq__(self, other):
        if type(other) is type(self):
            return self.address == other.address
        else:
            return False

    def __repr__(self):
        return f"<{self.__class__.__name__} at {hex(id(self))}>  {self.address} ({self.last_connection:.2f})"

    def __str__(self):
        return self.address

    def __call__(self, *args, **kwargs):
        return self.address

    def __hash__(self):
        return hash((self.address, self.last_connection))

    def __format__(self, format_spec):
        return self.address.__format__(format_spec)

    def split(self, on):
        return self.address.split(on)

    def rsplit(self, on, maxsplit):
        return self.address.rsplit(on, maxsplit)
