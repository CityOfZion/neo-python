from unittest import TestCase
import logging

class NeoTestCase(TestCase):


    def setUp(self):
        logname = 'prompt.log'
        logging.basicConfig(
            level=logging.DEBUG,
            filemode='a',
            filename=logname,
            format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")
