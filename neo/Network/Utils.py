from twisted.internet import task, interfaces, defer
from zope.interface import implementer
from twisted.test import proto_helpers
from twisted.internet.endpoints import _WrappingFactory
import socket
import ipaddress


class LoopingCall(task.LoopingCall):
    """
    A testable looping call
    """

    def __init__(self, *a, **kw):
        if 'clock' in kw:
            clock = kw['clock']
            del kw['clock']
        super(LoopingCall, self).__init__(*a, **kw)

        self.clock = clock


@implementer(interfaces.IStreamClientEndpoint)
class TestTransportEndpoint(object):
    """
    Helper class for testing
    """

    def __init__(self, reactor, addr, tr=None):
        self.reactor = reactor
        self.addr = addr
        self.tr = proto_helpers.StringTransport()
        if tr:
            self.tr = tr

    def connect(self, protocolFactory):
        """
        Implement L{IStreamClientEndpoint.connect} to connect via StringTransport.
        """
        try:
            node = protocolFactory.buildProtocol((self.addr))
            node.makeConnection(self.tr)
            # because the Twisted `StringTransportWithDisconnection` helper class tries to weirdly enough access `protocol` on a transport
            self.tr.protocol = node
            return defer.succeed(node)
        except Exception:
            return defer.fail()


def hostname_to_ip(hostname):
    return socket.gethostbyname(hostname)


def is_ip_address(hostname):
    host = hostname.split(':')[0]
    try:
        ip = ipaddress.ip_address(host)
        return True
    except ValueError:
        return False
