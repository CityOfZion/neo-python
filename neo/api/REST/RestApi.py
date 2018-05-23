"""
The REST API is using the Python package 'klein', which makes it possible to
create HTTP routes and handlers with Twisted in a similar style to Flask:
https://github.com/twisted/klein

"""
import json
from klein import Klein
from logzero import logger

from neo.Network.NodeLeader import NodeLeader
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neo.Settings import settings
from neo.api.utils import cors_header


API_URL_PREFIX = "/v1"


class RestApi:
    app = Klein()
    notif = None

    def __init__(self):
        self.notif = NotificationDB.instance()

    #
    # REST API Routes
    #
    @app.route('/')
    def home(self, request):
        endpoints_html = """<ul>
            <li><pre>{apiPrefix}/notifications/block/&lt;height&gt;</pre> <em>notifications by block</em></li>
            <li><pre>{apiPrefix}/notifications/addr/&lt;addr&gt;</pre><em>notifications by address</em></li>
            <li><pre>{apiPrefix}/notifications/tx/&lt;hash&gt;</pre><em>notifications by tx</em></li>
            <li><pre>{apiPrefix}/notifications/contract/&lt;hash&gt;</pre><em>notifications by contract</em></li>
            <li><pre>{apiPrefix}/tokens</pre><em>lists all NEP5 Tokens</em></li>
            <li><pre>{apiPrefix}/token/&lt;contract_hash&gt;</pre><em>list an NEP5 Token</em></li>
            <li><pre>{apiPrefix}/status</pre> <em>current block height and version</em></li>
        </ul>
        """.format(apiPrefix=API_URL_PREFIX)

        return """<html>
                    <style>body {padding:20px;max-width:800px;pre { background-color:#eee; }</style>
                    <body>
                        <p>
                            <h2>REST API for NEO %s</h2>
                            (see also <a href="https://github.com/CityOfZion/neo-python">neo-python</a>, <a href="https://github.com/CityOfZion/neo-python/blob/development/api-server.py">api-server.py</a>)
                        </p>

                        <hr/>

                        <h2>endpoints:</h2>
                        <p>%s</p>
                        <div>
                            <hr/>
                            <h3>pagination</h3>
                            <p>results are offered in page size of 500</p>
                            <p>you may request a different page by specifying the <code>page</code> query string param, for example:</p>
                            <pre>/block/123456?page=3</pre>
                            <p>page index starts at 0, so the 2nd page would be <code>?page=1</code></p>
                            <hr/>
                            <h3>sample output</h3>
                            <pre>
{
    "page_len": 1000,
    "total": 4,
    "page": 0,
    "current_height": 982506,
    "results": [
        {
            "type": "SmartContract.Runtime.Notify",
            "contract": "400cbed5b41014788d939eaf6286e336e7140f8c",
            "tx": "d0805fd7ec19a4a414374ae3720447d2576659053eb7588b85a0f9f1fd629791",
            "block": 928119,
            "addr_from": "AUYSKFEWPZxP57fo3TsK6Lwg22qxSFupKF",
            "amount": 1,
            "addr_to": "ALULT5WpeiHnEXYFe72Yq7nRB3ZBmsBypq",
            "notify_type": "transfer"
        },
        {
            "type": "SmartContract.Runtime.Notify",
            "contract": "d3de84c166d93ad2581cb587bda8e02b12dc37ca",
            "tx": "667df082eaa16ce2b07e48e214eb019b3e9450e76daea4f5b0450578a07836ef",
            "block": 936352,
            "addr_from": "ALULT5WpeiHnEXYFe72Yq7nRB3ZBmsBypq",
            "amount": 1,
            "addr_to": "AaD74SkQXsSE7UtSutQ4VV3mRdQUoMk98X",
            "notify_type": "transfer"
        },
        {
            "type": "SmartContract.Runtime.Notify",
            "contract": "2c0fdfa9592814b0a938219e218e3a6b08615acd",
            "tx": "eda792e7814e128eecda992f78a11577ee0604827de4aa91ffcda4616c889191",
            "block": 939449,
            "addr_from": "ALULT5WpeiHnEXYFe72Yq7nRB3ZBmsBypq",
            "amount": 1,
            "addr_to": "AaVgSU9vEPdwc49rPrCyj1LYkpsGFNgbjy",
            "notify_type": "transfer"
        },
        {
            "type": "SmartContract.Runtime.Notify",
            "contract": "f9572c5b119a6b5775a6af07f1cef5d310038f55",
            "tx": "6d0f1decbf3874d08d41f2cc9e8672cd3507c962668c15793e3dd3e01fc3551c",
            "block": 942369,
            "addr_from": "ALULT5WpeiHnEXYFe72Yq7nRB3ZBmsBypq",
            "amount": 1,
            "addr_to": "APaGQT4dx4gUDApVPnbtZvChJ8UKRsZBdt",
            "notify_type": "transfer"
        }
    ],
    "message": ""
}</pre>
                        </div>
                    </body>
                </html>""" % (settings.net_name, endpoints_html)

    @app.route('%s/notifications/block/<int:block>' % API_URL_PREFIX, methods=['GET'])
    @cors_header
    def get_by_block(self, request, block):
        request.setHeader('Content-Type', 'application/json')
        try:
            if int(block) > Blockchain.Default().Height:
                return self.format_message("Higher than current block")
            else:
                notifications = self.notif.get_by_block(block)
        except Exception as e:
            logger.info("Could not get notifications for block %s %s" % (block, e))
            return self.format_message("Could not get notifications for block %s because %s " % (block, e))
        return self.format_notifications(request, notifications)

    @app.route('%s/notifications/addr/<string:address>' % API_URL_PREFIX, methods=['GET'])
    @cors_header
    def get_by_addr(self, request, address):
        request.setHeader('Content-Type', 'application/json')
        try:
            notifications = self.notif.get_by_addr(address)
        except Exception as e:
            logger.info("Could not get notifications for address %s " % address)
            return self.format_message("Could not get notifications for address %s because %s" % (address, e))
        return self.format_notifications(request, notifications)

    @app.route('%s/notifications/tx/<string:tx_hash>' % API_URL_PREFIX, methods=['GET'])
    @cors_header
    def get_by_tx(self, request, tx_hash):
        request.setHeader('Content-Type', 'application/json')

        bc = Blockchain.Default()  # type: Blockchain
        notifications = []
        try:
            hash = UInt256.ParseString(tx_hash)
            tx, height = bc.GetTransaction(hash)
            if not tx:
                return self.format_message("Could not find transaction for hash %s" % (tx_hash))
            block_notifications = self.notif.get_by_block(height - 1)
            for n in block_notifications:
                if n.tx_hash == tx.Hash:
                    notifications.append(n)
        except Exception as e:
            logger.info("Could not get tx with hash %s because %s " % (tx_hash, e))
            return self.format_message("Could not get tx with hash %s because %s " % (tx_hash, e))

        return self.format_notifications(request, notifications)

    @app.route('%s/notifications/contract/<string:contract_hash>' % API_URL_PREFIX, methods=['GET'])
    @cors_header
    def get_by_contract(self, request, contract_hash):
        request.setHeader('Content-Type', 'application/json')
        try:
            hash = UInt160.ParseString(contract_hash)
            notifications = self.notif.get_by_contract(hash)
        except Exception as e:
            logger.info("Could not get notifications for contract %s " % contract_hash)
            return self.format_message("Could not get notifications for contract hash %s because %s" % (contract_hash, e))
        return self.format_notifications(request, notifications)

    @app.route('%s/tokens' % API_URL_PREFIX, methods=['GET'])
    @cors_header
    def get_tokens(self, request):
        request.setHeader('Content-Type', 'application/json')
        notifications = self.notif.get_tokens()
        return self.format_notifications(request, notifications)

    @app.route('%s/token/<string:contract_hash>' % API_URL_PREFIX, methods=['GET'])
    @cors_header
    def get_token(self, request, contract_hash):
        request.setHeader('Content-Type', 'application/json')
        try:
            uint160 = UInt160.ParseString(contract_hash)
            contract_event = self.notif.get_token(uint160)
            if not contract_event:
                return self.format_message("Could not find contract with hash %s" % contract_hash)
            notifications = [contract_event]
        except Exception as e:
            logger.info("Could not get contract with hash %s because %s " % (contract_hash, e))
            return self.format_message("Could not get contract with hash %s because %s " % (contract_hash, e))

        return self.format_notifications(request, notifications)

    @app.route('%s/status' % API_URL_PREFIX, methods=['GET'])
    @cors_header
    def get_status(self, request):
        request.setHeader('Content-Type', 'application/json')
        return json.dumps({
            'current_height': Blockchain.Default().Height,
            'version': settings.VERSION_NAME,
            'num_peers': len(NodeLeader.Instance().Peers)
        }, indent=4, sort_keys=True)

    def format_notifications(self, request, notifications, show_none=False):
        notif_len = len(notifications)
        page_len = 500
        page = 0
        message = ''
        if b'page' in request.args:
            try:
                page = int(request.args[b'page'][0])
            except Exception as e:
                print("could not get page: %s" % e)

        start = page_len * page
        end = start + page_len

        if start > notif_len:
            message = 'page greater than result length'

        notifications = notifications[start:end]

        return json.dumps({
            'current_height': Blockchain.Default().Height + 1,
            'message': message,
            'total': notif_len,
            'results': None if show_none else [n.ToJson() for n in notifications],
            'page': page,
            'page_len': page_len
        }, indent=4, sort_keys=True)

    def format_message(self, message):
        return json.dumps({
            'current_height': Blockchain.Default().Height + 1,
            'message': message,
            'total': 0,
            'results': None,
            'page': 0,
            'page_len': 0
        }, indent=4, sort_keys=True)
