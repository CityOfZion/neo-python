import asynctest
import asyncio
import os
from logging import DEBUG
from neo.Network.syncmanager import SyncManager
from neo.Network.flightinfo import FlightInfo
from neo.Network.requestinfo import RequestInfo
from neo.Network.core.header import Header
from neo.Network.ledger import Ledger
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
from neo.Network.core.uint256 import UInt256
from neo.Network.core.uint160 import UInt160


class HeadersReceivedSyncMgrTestCase(BlockchainFixtureTestCase, asynctest.TestCase):
    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self) -> None:
        # we have to override the singleton behaviour or our coroutine mocks will persist
        with asynctest.patch('neo.Network.syncmanager.SyncManager.__new__', return_value=object.__new__(SyncManager)):
            self.syncmgr = SyncManager()
            self.syncmgr.init(asynctest.MagicMock)
            self.syncmgr.reset()

    async def test_empty_header_list(self):
        res = await self.syncmgr.on_headers_received(123, [])
        self.assertEqual(res, -1)

    async def test_unexpected_headers_received(self):
        # headers received while we have no outstanding request should be early ignored

        self.syncmgr.header_request = None
        res = await self.syncmgr.on_headers_received(123, [object()])
        self.assertEqual(res, -2)

    async def test_headers_received_not_matching_requested_height(self):
        cur_header_height = 1
        node_id = 123

        self.syncmgr.header_request = RequestInfo(cur_header_height + 1)
        self.syncmgr.header_request.add_new_flight(FlightInfo(node_id, cur_header_height + 1))

        height = 123123
        header = Header(object(), object(), 0, height, object(), object(), object())
        res = await self.syncmgr.on_headers_received(123, [header])
        self.assertEqual(res, -3)

    async def test_headers_received_outdated_height(self):
        # test that a slow response that has been superseeded by a fast response
        # from another node does not get processed twice
        cur_header_height = 1
        node_id = 123

        self.syncmgr.header_request = RequestInfo(cur_header_height + 1)
        self.syncmgr.header_request.add_new_flight(FlightInfo(node_id, cur_header_height + 1))

        height = 2
        header = Header(object(), object(), 0, height, object(), object(), object())

        # mock ledger state
        self.syncmgr.ledger = asynctest.MagicMock()
        self.syncmgr.ledger.cur_header_height = asynctest.CoroutineMock(return_value=2)

        with self.assertLogHandler('syncmanager', DEBUG) as log_context:
            res = await self.syncmgr.on_headers_received(123, [header])
            self.assertEqual(res, -5)
            self.assertGreater(len(log_context.output), 0)
            self.assertTrue("Headers received 2 - 2" in log_context.output[0])


class HeadersReceivedSyncMgrTestCase2(BlockchainFixtureTestCase, asynctest.TestCase):
    """
    For the final test we need to use a new fixture
    """

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self) -> None:
        # we have to override the singleton behaviour or our coroutine mocks will persist
        with asynctest.patch('neo.Network.syncmanager.SyncManager.__new__', return_value=object.__new__(SyncManager)):
            self.syncmgr = SyncManager()
            self.syncmgr.init(asynctest.MagicMock)
            self.syncmgr.reset()

    def test_simultaneous_same_header_received(self):
        """
        test ensures that we do not waste computing sources processing the same headers multiple times
        expected result is 1 "processed" event (return value 1) and 4 early exit events (return value -4)
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.syncmgr.ledger = Ledger()
        self.syncmgr.nodemgr.add_node_error_count = asynctest.CoroutineMock()

        height = 12357
        node_id = 123

        self.syncmgr.header_request = RequestInfo(height)
        self.syncmgr.header_request.add_new_flight(FlightInfo(node_id, height))

        fake_uint256 = UInt256(data=bytearray(32))
        fake_uint160 = UInt160(data=bytearray(20))
        not_used = object()

        # create 2000 headers that can be persisted
        headers = []
        for i in range(2000):
            headers.append(Header(fake_uint256, fake_uint256, 0, height + i, 0, fake_uint160, not_used))

        # create 5 tasks to schedule incoming headers
        tasks = []
        for i in range(5):
            tasks.append(loop.create_task(self.syncmgr.on_headers_received(i, headers)))

        # run all tasks
        try:
            results = loop.run_until_complete(asyncio.gather(*tasks))
        finally:
            loop.close()

        # assert that only the first one gets fully processed, the rest not
        success = 1
        already_exist = -4
        expected_results = [success, already_exist, already_exist, already_exist, already_exist]
        self.assertEqual(results, expected_results)
