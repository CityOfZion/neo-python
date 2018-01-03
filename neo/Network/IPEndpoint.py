class IPEndpoint():
    ANY = '0.0.0.0'

    Address = None
    Port = None

    def __init__(self, addr, port):
        """
        Create instance.
        Args:
            addr (str):
            port (int):
        """
        self.Address = addr
        self.Port = port

    def ToAddress(self):
        """
        Get the string representation of the endpoint.

        Returns:
            str: address:port
        """
        return '%s:%s' % (self.Address, self.Port)
