import os
from unittest import TestCase
from examples.build_raw_transactions import example1, example2


class BuildRawTransactionsTestCase(TestCase):

    def test_example1(self):
        res = example1()

        self.assertTrue(res)
        self.assertEqual(res.decode('utf-8'), "80000190274d792072617720636f6e7472616374207472616e73616374696f6e206465736372697074696f6e01949354ea0a8b57dfee1e257a1aedd1e0eea2e5837de145e8da9c0f101bfccc8e0100029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500a3e11100000000ea610aa6db39bd8c8556c9569d94b5e5a5d0ad199b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc5004f2418010000001cc9c05cefffe6cdd7b182816a9152ec218d2ec000")

        os.remove("path")

    def test_example2(self):
        res = example2()

        self.assertTrue(res)
        self.assertEqual(res.decode('utf-8'), "d1001b00046e616d6567d3d8602814a429a91afdbaa3914884a1c90c73310290274d792072617720636f6e7472616374207472616e73616374696f6e206465736372697074696f6e201cc9c05cefffe6cdd7b182816a9152ec218d2ec000000141405bd8ba993473b51bfa338dd3f2d4a236b4e940572cf6f077c411cd3a5fa8ccce09d945159a3978e7697915620473da0e2189048d768ed2a70535a73a9cba3a33232103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac")

        os.remove("path")
