import unittest
from neo.Network.ipfilter import IPFilter


class IPFilteringTestCase(unittest.TestCase):
    def test_nobody_allowed(self):
        filter = IPFilter()
        filter.config = {
            'blacklist': [
                '0.0.0.0/0'
            ],
            'whitelist': [
            ]
        }

        self.assertFalse(filter.is_allowed('127.0.0.1'))
        self.assertFalse(filter.is_allowed('10.10.10.10'))

    def test_nobody_allowed_except_one(self):
        filter = IPFilter()
        filter.config = {
            'blacklist': [
                '0.0.0.0/0'
            ],
            'whitelist': [
                '10.10.10.10'
            ]
        }

        self.assertFalse(filter.is_allowed('127.0.0.1'))
        self.assertFalse(filter.is_allowed('10.10.10.11'))
        self.assertTrue(filter.is_allowed('10.10.10.10'))

    def test_everybody_allowed(self):
        filter = IPFilter()
        filter.config = {
            'blacklist': [
            ],
            'whitelist': [
            ]
        }

        self.assertTrue(filter.is_allowed('127.0.0.1'))
        self.assertTrue(filter.is_allowed('10.10.10.11'))
        self.assertTrue(filter.is_allowed('10.10.10.10'))

        filter.config = {
            'blacklist': [
            ],
            'whitelist': [
                '0.0.0.0/0'
            ]
        }

        self.assertTrue(filter.is_allowed('127.0.0.1'))
        self.assertTrue(filter.is_allowed('10.10.10.11'))
        self.assertTrue(filter.is_allowed('10.10.10.10'))

        filter.config = {
            'blacklist': [
                '0.0.0.0/0'
            ],
            'whitelist': [
                '0.0.0.0/0'
            ]
        }

        self.assertTrue(filter.is_allowed('127.0.0.1'))
        self.assertTrue(filter.is_allowed('10.10.10.11'))
        self.assertTrue(filter.is_allowed('10.10.10.10'))

    def test_everybody_allowed_except_one(self):
        filter = IPFilter()
        filter.config = {
            'blacklist': [
                '127.0.0.1'
            ],
            'whitelist': [
            ]
        }

        self.assertFalse(filter.is_allowed('127.0.0.1'))
        self.assertTrue(filter.is_allowed('10.10.10.11'))
        self.assertTrue(filter.is_allowed('10.10.10.10'))

    def test_disallow_ip_range(self):
        filter = IPFilter()
        filter.config = {
            'blacklist': [
                '127.0.0.0/24'
            ],
            'whitelist': [
            ]
        }

        self.assertFalse(filter.is_allowed('127.0.0.0'))
        self.assertFalse(filter.is_allowed('127.0.0.1'))
        self.assertFalse(filter.is_allowed('127.0.0.100'))
        self.assertFalse(filter.is_allowed('127.0.0.255'))
        self.assertTrue(filter.is_allowed('10.10.10.11'))
        self.assertTrue(filter.is_allowed('10.10.10.10'))

    def test_updating_blacklist(self):
        filter = IPFilter()
        filter.config = {
            'blacklist': [
            ],
            'whitelist': [
            ]
        }

        self.assertTrue(filter.is_allowed('127.0.0.1'))

        filter.blacklist_add('127.0.0.0/24')
        self.assertFalse(filter.is_allowed('127.0.0.1'))
        # should have no effect, only exact matches
        filter.blacklist_remove('127.0.0.1')
        self.assertFalse(filter.is_allowed('127.0.0.1'))

        filter.blacklist_remove('127.0.0.0/24')
        self.assertTrue(filter.is_allowed('127.0.0.1'))

    def test_updating_whitelist(self):
        filter = IPFilter()
        filter.config = {
            'blacklist': [
                '0.0.0.0/0'
            ],
            'whitelist': [
            ]
        }

        self.assertFalse(filter.is_allowed('127.0.0.1'))

        filter.whitelist_add('127.0.0.0/24')
        self.assertTrue(filter.is_allowed('127.0.0.1'))

        filter.whitelist_remove('127.0.0.1')
        # should have no effect, only exact matches
        self.assertTrue(filter.is_allowed('127.0.0.1'))

        filter.whitelist_remove('127.0.0.0/24')
        self.assertFalse(filter.is_allowed('127.0.0.1'))
