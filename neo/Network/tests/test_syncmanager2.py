import asynctest
from logging import DEBUG
from neo.Network.syncmanager import SyncManager
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Network.flightinfo import FlightInfo
from neo.Network.requestinfo import RequestInfo
from neo.Network.nodemanager import NeoNode


class TimeoutSyncMgrTestCase(NeoTestCase, asynctest.TestCase):
    def setUp(self) -> None:
        # we have to override the singleton behaviour or our coroutine mocks will persist
        with asynctest.patch('neo.Network.syncmanager.SyncManager.__new__', return_value=object.__new__(SyncManager)):
            self.syncmgr = SyncManager()
            self.syncmgr.init(asynctest.MagicMock)
            self.syncmgr.reset()

    async def test_header_exception(self):
        self.syncmgr.check_block_timeout = asynctest.CoroutineMock()

        self.syncmgr.check_header_timeout = asynctest.CoroutineMock()
        self.syncmgr.check_header_timeout.side_effect = Exception("unittest exception")

        with self.assertLogHandler('syncmanager', DEBUG) as context:
            await self.syncmgr.check_timeout()
            self.assertGreater(len(context.output), 0)
            self.assertTrue("unittest exception" in context.output[0])

    async def test_block_exception(self):
        self.syncmgr.check_block_timeout = asynctest.CoroutineMock()
        self.syncmgr.check_block_timeout.side_effect = Exception("unittest exception")

        self.syncmgr.check_header_timeout = asynctest.CoroutineMock()

        with self.assertLogHandler('syncmanager', DEBUG) as context:
            await self.syncmgr.check_timeout()
            self.assertGreater(len(context.output), 0)
            self.assertTrue("unittest exception" in context.output[0])

    async def test_no_outstanding_header_requests(self):
        # should return immediately
        self.syncmgr.header_request = asynctest.MagicMock()
        self.syncmgr.header_request.__bool__.return_value = False
        await self.syncmgr.check_timeout()

        self.assertFalse(self.syncmgr.header_request.most_recent_flight.called)

    async def test_outstanding_header_request_within_boundaries(self):
        # should return early because we have not exceeded the threshold
        cur_header_height = 1
        node_id = 123

        self.syncmgr.nodemgr = asynctest.MagicMock()
        self.syncmgr.header_request = RequestInfo(cur_header_height + 1)
        self.syncmgr.header_request.add_new_flight(FlightInfo(node_id, cur_header_height + 1))

        await self.syncmgr.check_timeout()

        self.assertFalse(self.syncmgr.nodemgr.get_node_by_nodeid.called)

    async def test_outstanding_header_request_timedout_but_received(self):
        """
        test an outstanding request that timedout, but has been received in the meantime
        """
        cur_header_height = 1
        node_id = 123

        # mock node manager state
        self.syncmgr.nodemgr = asynctest.MagicMock()
        node1 = NeoNode(object(), object())
        node1.nodeid = node_id
        self.syncmgr.nodemgr.get_node_by_id.return_value = node1

        # mock ledger state
        self.syncmgr.ledger = asynctest.MagicMock()
        # we pretend our local ledger has a height higher than what we just asked for
        self.syncmgr.ledger.cur_header_height = asynctest.CoroutineMock(return_value=3)

        # setup sync manager state to have an outstanding header request
        self.syncmgr.header_request = RequestInfo(cur_header_height + 1)
        fi = FlightInfo(node_id, cur_header_height + 1)
        fi.start_time = fi.start_time - 5  # decrease start time by 5 seconds to exceed timeout threshold
        self.syncmgr.header_request.add_new_flight(fi)

        with self.assertLogHandler('syncmanager', DEBUG) as log_context:
            await self.syncmgr.check_timeout()
            self.assertGreater(len(log_context.output), 0)
            self.assertTrue("Header timeout limit exceed" in log_context.output[0])

        self.assertIsNone(self.syncmgr.header_request)

    async def test_outstanding_header_request_timedout(self):
        """
        test an outstanding request that timedout, but for which we cannot ask another node
        conditions:
        - current node exceeded MAX_TIMEOUT_COUNT and will be disconencted
        - no other nodes are connected that have our desired height

        Expected:
        We expect to return without setting up another header request with a new node. The node manager
        should resolve getting new nodes
        """
        cur_header_height = 1
        node_id = 123

        # mock node manager state
        self.syncmgr.nodemgr = asynctest.MagicMock()
        node1 = NeoNode(object(), object())
        node1.nodeid = node_id
        self.syncmgr.nodemgr.get_node_by_id.return_value = node1
        # returning None indicates we have no more nodes connected with our desired height
        self.syncmgr.nodemgr.get_node_with_min_failed_time.return_value = None
        self.syncmgr.nodemgr.add_node_timeout_count = asynctest.CoroutineMock()
        # -------

        # mock ledger state
        self.syncmgr.ledger = asynctest.MagicMock()
        # we pretend our local ledger has a height higher than what we just asked for
        self.syncmgr.ledger.cur_header_height = asynctest.CoroutineMock(return_value=1)
        # ------

        # setup sync manager state to have an outstanding header request
        self.syncmgr.header_request = RequestInfo(cur_header_height + 1)
        fi = FlightInfo(node_id, cur_header_height + 1)
        fi.start_time = fi.start_time - 5  # decrease start time by 5 seconds to exceed timeout threshold
        self.syncmgr.header_request.add_new_flight(fi)

        with self.assertLogHandler('syncmanager', DEBUG) as log_context:
            await self.syncmgr.check_timeout()
            self.assertGreater(len(log_context.output), 0)
            self.assertTrue("Header timeout limit exceed" in log_context.output[0])

        self.assertTrue(self.syncmgr.nodemgr.get_node_with_min_failed_time.called)
        self.assertIsNone(self.syncmgr.header_request)

    async def test_outstanding_request_timedout(self):
        cur_header_height = 1
        node_id = 123

        # mock node manager state
        self.syncmgr.nodemgr = asynctest.MagicMock()
        node1 = NeoNode(object(), object())
        node1.nodeid = node_id
        self.syncmgr.nodemgr.get_node_by_id.return_value = node1

        node2 = asynctest.MagicMock()  # NeoNode(object(), object())
        node2.nodeid.return_value = 456
        node2.get_headers = asynctest.CoroutineMock()
        self.syncmgr.nodemgr.get_node_with_min_failed_time.return_value = node2
        self.syncmgr.nodemgr.add_node_timeout_count = asynctest.CoroutineMock()

        # mock ledger state
        self.syncmgr.ledger = asynctest.MagicMock()
        # we pretend our local ledger has a height higher than what we just asked for
        self.syncmgr.ledger.cur_header_height = asynctest.CoroutineMock(return_value=1)
        self.syncmgr.ledger.header_hash_by_height = asynctest.CoroutineMock(return_value=b'')
        # ------

        # setup sync manager state to have an outstanding header request
        self.syncmgr.header_request = RequestInfo(cur_header_height + 1)
        fi = FlightInfo(node_id, cur_header_height + 1)
        fi.start_time = fi.start_time - 5  # decrease start time by 5 seconds to exceed timeout threshold
        self.syncmgr.header_request.add_new_flight(fi)

        with self.assertLogHandler('syncmanager', DEBUG) as log_context:
            await self.syncmgr.check_timeout()
            self.assertGreater(len(log_context.output), 0)
            self.assertTrue("Retry requesting headers starting at 2" in log_context.output[-1])
