"""


The REST API is using the Python package 'klein', which makes it possible to
create HTTP routes and handlers with Twisted in a similar style to Flask:
https://github.com/twisted/klein

"""
import json
from klein import Klein
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from logzero import logger
from neo.Core.Blockchain import Blockchain


class NotificationServer(object):
    app = Klein()

    notif = None

    def __init__(self):

        self.notif = NotificationDB.instance()

    #
    # REST API Routes
    #
    @app.route('/')
    def home(self, request):

        return """<html>
                    <body>
                        <h2>Endpoints:</h2>
                            <p>
                                <ul>
                                    <li><pre>/block/{height}</pre></li>
                                    <li><pre>/addr/{addr}</pre></li>
                                    <li><pre>/tx/{hash}</pre></li>
                                </ul>
                            </p>
                    </body>
                </html>"""

    @app.route('/block/<int:block>')
    def get_by_block(self, request, block):
        request.setHeader('Content-Type', 'application/json')
        try:
            notifications = self.notif.get_by_block(block)
        except Exception as e:
            logger.info("Could not get notifications for block %s %s" % (block, e))
            return self.format_message("Could not get notifications for block %s because %s " % (block, e))
        return self.format_notifications(notifications)

    @app.route('/addr/<string:address>')
    def get_by_addr(self, request, address):
        request.setHeader('Content-Type', 'application/json')
        try:
            notifications = self.notif.get_by_addr(address)
        except Exception as e:
            logger.info("Could not get notifications for address %s " % address)
            return self.format_message("Could not get notifications for address %s because %s" % (address, e))
        return self.format_notifications(notifications)

    @app.route('/tx/<string:tx_hash>')
    def get_by_tx(self, request, tx_hash):
        request.setHeader('Content-Type', 'application/json')

        bc = Blockchain.Default()  # type: Blockchain
        notifications = []

        try:
            tx, height = bc.GetTransaction(tx_hash)

            block_notifications = self.notif.get_by_block(height - 1)

            for n in block_notifications:
                if n.tx_hash == tx.Hash:
                    notifications.append(n)
        except Exception as e:
            logger.info("Could not get tx with hash %s because %s " % (tx_hash, e))
            return self.format_message("Could not get tx with hash %s because %s " % (tx_hash, e))

        return self.format_notifications(notifications)

    def format_notifications(self, notifications):
        return json.dumps({
            'current_height': Blockchain.Default().Height,
            'message': '',
            'total': len(notifications),
            'results': [n.ToJson() for n in notifications]
        }, indent=4)

    def format_message(self, message):
        return json.dumps({
            'current_height': Blockchain.Default().Height,
            'message': message,
            'total': 0,
            'results': []
        }, indent=4)
