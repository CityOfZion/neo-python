import datetime


class Address:
    def __init__(self, address, lastConnectionTo=None):
        if not lastConnectionTo:
            self.last_connection = 0
        else:
            self.last_connection = lastConnectionTo

        self.address = address

    @classmethod
    def Now(cls):
        return datetime.datetime.utcnow().timestamp()

    def __eq__(self, other):
        if type(other) is type(self):
            return self.address == other.address
        else:
            return False

    def __repr__(self):
        return self.address

    def __call__(self, *args, **kwargs):
        return self.address

    def __hash__(self):
        return hash((self.address, self.last_connection))

    def __format__(self, format_spec):
        return self.address.__format__(format_spec)

    def split(self, on):
        return self.address.split(on)
