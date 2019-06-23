"""
The REST API is using the Python package 'aioHttp'
"""
import math

from neo.Implementations.Notifications.NotificationDB import NotificationDB
from neo.Core.Blockchain import Blockchain
from aiohttp import web
from logzero import logger
from neo.Core.UInt160 import UInt160
from neo.Core.UInt256 import UInt256

from neo.Network.nodemanager import NodeManager
from neo.Settings import settings
from neo.api.utils import json_response

API_URL_PREFIX = "/v1"


class RestApi:
    notif = None

    def __init__(self):
        self.notif = NotificationDB.instance()
        self.app = web.Application()
        self.app.add_routes([
            web.route('*', '/', self.home),
            web.get("/v1/notifications/block/{block}", self.get_by_block),
            web.get("/v1/notifications/addr/{address}", self.get_by_addr),
            web.get("/v1/notifications/tx/{tx_hash}", self.get_by_tx),
            web.get("/v1/notifications/contract/{contract_hash}", self.get_by_contract),
            web.get("/v1/token/{contract_hash}", self.get_token),
            web.get("/v1/tokens", self.get_tokens),
            web.get("/v1/status", self.get_status)
        ])

    #
    # REST API Routes
    #
    async def home(self, request):
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

        out = """<html>
                    <style>body {padding:20px;max-width:800px;pre { background-color:#eee; }</style>
                    <body>
                        <p>
                            <h2>REST API for NEO %s</h2>
                            (see also <a href="https://github.com/CityOfZion/neo-python">neo-python</a>,
                                      <a href="https://github.com/CityOfZion/neo-python/blob/development/api-server.py">api-server.py</a>)
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
    "total_pages": 1,
    "total": 4,
    "page": 1,
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
        return web.Response(text=out, content_type="text/html")

    @json_response
    async def get_by_block(self, request):
        try:
            block = request.match_info['block']
            if int(block) > Blockchain.Default().Height:
                return self.format_message("Higher than current block")
            else:
                notifications = self.notif.get_by_block(int(block))
        except Exception as e:
            logger.info("Could not get notifications for block %s %s" % (block, e))
            return self.format_message("Could not get notifications for block %s because %s " % (block, e))
        x = self.format_notifications(request, notifications)
        return x

    @json_response
    async def get_by_addr(self, request):
        try:
            address = request.match_info['address']
            notifications = self.notif.get_by_addr(address)
        except Exception as e:
            logger.info("Could not get notifications for address %s " % address)
            return self.format_message("Could not get notifications for address %s because %s" % (address, e))
        return self.format_notifications(request, notifications)

    @json_response
    async def get_by_tx(self, request):
        tx_hash = request.match_info['tx_hash']
        bc = Blockchain.Default()  # type: Blockchain
        notifications = []
        try:
            hash = UInt256.ParseString(tx_hash)
            tx, height = bc.GetTransaction(hash)
            if not tx:
                return self.format_message("Could not find transaction for hash %s" % (tx_hash))
            block_notifications = self.notif.get_by_block(height)
            for n in block_notifications:
                if n.tx_hash == tx.Hash:
                    notifications.append(n)
        except Exception as e:
            logger.info("Could not get tx with hash %s because %s " % (tx_hash, e))
            return self.format_message("Could not get tx with hash %s because %s " % (tx_hash, e))

        return self.format_notifications(request, notifications)

    @json_response
    async def get_by_contract(self, request):
        contract_hash = request.match_info['contract_hash']
        try:
            hash = UInt160.ParseString(contract_hash)
            notifications = self.notif.get_by_contract(hash)
        except Exception as e:
            logger.info("Could not get notifications for contract %s " % contract_hash)
            return self.format_message("Could not get notifications for contract hash %s because %s" % (contract_hash, e))
        return self.format_notifications(request, notifications)

    @json_response
    async def get_tokens(self, request):
        notifications = self.notif.get_tokens()
        return self.format_notifications(request, notifications)

    @json_response
    async def get_token(self, request):
        contract_hash = request.match_info['contract_hash']
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

    @json_response
    async def get_status(self, request):
        return {
            'current_height': Blockchain.Default().Height,
            'version': settings.VERSION_NAME,
            'num_peers': len(NodeManager().nodes)
        }

    def format_notifications(self, request, notifications, show_none=False):

        notif_len = len(notifications)
        page_len = 500
        page = 1
        message = ''
        if 'page' in request.query:
            try:
                page = int(request.query['page'])
            except Exception as e:
                print("could not get page: %s" % e)
        if 'pagesize' in request.query:
            try:
                page_len = int(request.query['pagesize'])
            except Exception as e:
                print("could not get page length: %s" % e)

        # note, we want pages to start from 1, not 0, to be
        # in sync with C# version
        # we'll also convert page 0 to page1
        if page == 0:
            page = 1

        start = page_len * (page - 1)
        end = start + page_len

        if start > notif_len:
            message = 'page greater than result length'

        notifications = notifications[start:end]
        total_pages = math.ceil(notif_len / page_len)

        return {
            'current_height': Blockchain.Default().Height,
            'message': message,
            'total': notif_len,
            'results': None if show_none else [n.ToJson() for n in notifications],
            'page': page,
            'page_len': page_len,
            'total_pages': total_pages
        }

    def format_message(self, message):
        return {
            'current_height': Blockchain.Default().Height,
            'message': message,
            'total': 0,
            'results': None,
            'page': 0,
            'page_len': 0,
            'total_pages': 0
        }
