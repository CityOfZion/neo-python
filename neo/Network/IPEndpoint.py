

class IPEndpoint():

    ANY = '0.0.0.0'

    Address = None
    Port = None

    def __init__(self, addr, port):
        self.Address = addr
        self.Port = port

    def ToAddress(self):
        return '%s:%s' % (self.Address, self.Port)
