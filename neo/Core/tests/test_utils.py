from unittest import TestCase
from neo.Core.Utils import isValidPublicAddress


class UtilsTest(TestCase):
    def test_public_address_validator(self):
        # address too short
        self.assertFalse(isValidPublicAddress("aaa"))

        # address too long
        self.assertFalse(isValidPublicAddress("a" * 40))

        # address with invalid checksum
        self.assertFalse(isValidPublicAddress("AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEA"))

        # valid address
        self.assertTrue(isValidPublicAddress("AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg"))
