import asynctest
import asyncio
import os
from logging import DEBUG
from neo.Network.neonetwork.network.syncmanager import SyncManager
from neo.Network.neonetwork.network.flightinfo import FlightInfo
from neo.Network.neonetwork.network.requestinfo import RequestInfo
from neo.Network.neonetwork.core.header import Header
from neo.Network.neonetwork.ledger import Ledger
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
from neo.Network.neonetwork.core.uint256 import UInt256
from neo.Network.neonetwork.core.uint160 import UInt160
from datetime import datetime


class HeadersReceivedSyncMgrTestCase(BlockchainFixtureTestCase, asynctest.TestCase):
    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self) -> None:
        # we have to override the singleton behaviour or our coroutine mocks will persist
        with asynctest.patch('neo.Network.neonetwork.network.syncmanager.SyncManager.__new__', return_value=object.__new__(SyncManager)):
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

    async def test_headers_failed_to_add(self):
        """
        We supply 2 headers with the same index/height
        The first should be added, the second rejected

        Note: actually writes data to the fixture DB
        """
        self.syncmgr.ledger = Ledger()
        self.syncmgr.nodemgr.add_node_error_count = asynctest.CoroutineMock()

        height = 12357
        node_id = 123

        self.syncmgr.header_request = RequestInfo(height)
        self.syncmgr.header_request.add_new_flight(FlightInfo(node_id, height))

        fake_uint256 = UInt256(data=bytearray(32))
        fake_uint160 = UInt160(data=bytearray(20))
        not_used = object()
        header = Header(fake_uint256, fake_uint256, 0, height, 0, fake_uint160, not_used)

        with asynctest.patch('neo.Core.Blockchain.Blockchain.AddHeaders', return_value=0):
            with self.assertLogHandler('syncmanager', DEBUG) as log_context:
                await self.syncmgr.on_headers_received(123, [header, header])
                self.assertGreater(len(log_context.output), 1)
                self.assertIn("Failed to add all headers. Successfully added 1 out of 2", log_context.output[-2])


class HeadersReceivedSyncMgrTestCase2(BlockchainFixtureTestCase, asynctest.TestCase):
    """
    For the final test we need to use a new fixture
    """

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self) -> None:
        # we have to override the singleton behaviour or our coroutine mocks will persist
        with asynctest.patch('neo.Network.neonetwork.network.syncmanager.SyncManager.__new__', return_value=object.__new__(SyncManager)):
            self.syncmgr = SyncManager()
            self.syncmgr.init(asynctest.MagicMock)
            self.syncmgr.reset()

    async def test_headers_add_ok(self):
        """
        We supply 2 headers with the same index/height
        The first should be added, the second rejected
        """
        self.syncmgr.ledger = Ledger()
        self.syncmgr.nodemgr.add_node_error_count = asynctest.CoroutineMock()

        height = 12357
        node_id = 123

        self.syncmgr.header_request = RequestInfo(height)
        self.syncmgr.header_request.add_new_flight(FlightInfo(node_id, height))

        fake_uint256 = UInt256(data=bytearray(32))
        fake_uint160 = UInt160(data=bytearray(20))
        not_used = object()
        header1 = Header(fake_uint256, fake_uint256, 0, height, 0, fake_uint160, not_used)
        header2 = Header(fake_uint256, fake_uint256, 0, height + 1, 0, fake_uint160, not_used)

        with asynctest.patch('neo.Core.Blockchain.Blockchain.AddHeaders', return_value=0):
            with self.assertLogHandler('syncmanager', DEBUG) as log_context:
                await self.syncmgr.on_headers_received(123, [header1, header2])
                self.assertGreater(len(log_context.output), 1)
                self.assertNotIn("Failed to add all headers. Successfully added 1 out of 2", log_context.output[-2])
                self.assertFalse(self.syncmgr.nodemgr.add_node_error_count.called)


class HeadersReceivedSyncMgrTestCase3(BlockchainFixtureTestCase, asynctest.TestCase):
    """
    For the final test we need to use a new fixture
    """

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self) -> None:
        # we have to override the singleton behaviour or our coroutine mocks will persist
        with asynctest.patch('neo.Network.neonetwork.network.syncmanager.SyncManager.__new__', return_value=object.__new__(SyncManager)):
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
        already_persisting = -4
        expected_results = [success, already_persisting, already_persisting, already_persisting, already_persisting]
        self.assertEqual(results, expected_results)
