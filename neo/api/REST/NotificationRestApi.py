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
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256


class NotificationRestApi(object):
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
                    <style>body {padding:20px;max-width:800px;pre { background-color:#eee; }</style>
                    <body>
                        <h2>endpoints:</h2>
                        <p>
                            <ul>
                                <li><pre>/block/{height}</pre></li>
                                <li><pre>/addr/{addr}</pre></li>
                                <li><pre>/tx/{hash}</pre></li>
                                <li><pre>/tx/{hash}</pre></li>
                                <li><pre>/tokens</pre></li>
                                <li><pre>/token/{contract_hash}</pre></li>                                
                            </ul>
                        </p>
                        <div>
                            <hr/>
                            <h3>pagination</h3>
                            <p>results are offered in page size of 1000</p>
                            <p>you may request a different page by specifying the <code>page</code> query string param, for example:</p>
                            <pre>/block/123456?page=3</pre>
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
                </html>"""

    @app.route('/block/<int:block>', methods=['GET'])
    def get_by_block(self, request, block):
        request.setHeader('Content-Type', 'application/json')
        try:
            notifications = self.notif.get_by_block(block)
        except Exception as e:
            logger.info("Could not get notifications for block %s %s" % (block, e))
            return self.format_message("Could not get notifications for block %s because %s " % (block, e))
        return self.format_notifications(request, notifications)

    @app.route('/addr/<string:address>', methods=['GET'])
    def get_by_addr(self, request, address):
        request.setHeader('Content-Type', 'application/json')
        try:
            notifications = self.notif.get_by_addr(address)
        except Exception as e:
            logger.info("Could not get notifications for address %s " % address)
            return self.format_message("Could not get notifications for address %s because %s" % (address, e))
        return self.format_notifications(request, notifications)

    @app.route('/tx/<string:tx_hash>', methods=['GET'])
    def get_by_tx(self, request, tx_hash):
        request.setHeader('Content-Type', 'application/json')

        bc = Blockchain.Default()  # type: Blockchain
        notifications = []
        try:
            hash = UInt256.ParseString(tx_hash)
            tx, height = bc.GetTransaction(hash)
            block_notifications = self.notif.get_by_block(height - 1)
            for n in block_notifications:
                if n.tx_hash == tx.Hash:
                    notifications.append(n)
        except Exception as e:
            logger.info("Could not get tx with hash %s because %s " % (tx_hash, e))
            return self.format_message("Could not get tx with hash %s because %s " % (tx_hash, e))

        return self.format_notifications(request, notifications)

    @app.route('/contract/<string:contract_hash>', methods=['GET'])
    def get_by_contract(self, request, contract_hash):
        request.setHeader('Content-Type', 'application/json')
        try:
            hash = UInt160.ParseString(contract_hash)
            notifications = self.notif.get_by_contract(hash)
        except Exception as e:
            logger.info("Could not get notifications for contract %s " % contract_hash)
            return self.format_message("Could not get notifications for contract hash %s because %s" % (contract_hash, e))
        return self.format_notifications(request, notifications)

    @app.route('/tokens', methods=['GET'])
    def get_tokens(self, request):
        request.setHeader('Content-Type', 'application/json')
        notifications = self.notif.get_tokens()
        return self.format_notifications(request, notifications)

    @app.route('/token/<string:contract_hash>', methods=['GET'])
    def get_token(self, request, contract_hash):
        request.setHeader('Content-Type', 'application/json')
        try:
            uint160 = UInt160.ParseString(contract_hash)
            contract_event = self.notif.get_token(uint160)
            notifications = [contract_event]
        except Exception as e:
            logger.info("Could not get contract with hash %s because %s " % (contract_hash, e))
            return self.format_message("Could not get contract with hash %s because %s " % (contract_hash, e))

        return self.format_notifications(request, notifications)

    def format_notifications(self, request, notifications):

        notif_len = len(notifications)
        page_len = 1000
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
            'current_height': Blockchain.Default().Height,
            'message': message,
            'total': notif_len,
            'results': [n.ToJson() for n in notifications],
            'page': page,
            'page_len': page_len
        }, indent=4, sort_keys=True)

    def format_message(self, message):
        return json.dumps({
            'current_height': Blockchain.Default().Height,
            'message': message,
            'total': 0,
            'results': [],
            'page': 0,
            'page_len': 0
        }, indent=4, sort_keys=True)
