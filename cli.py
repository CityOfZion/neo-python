import sys
import logging

logging.basicConfig(
     level=logging.DEBUG, stream=sys.stdout,
     format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")

from neo.Neo import CLI
CLI.OpenWallet('accound.db','sthaoesutnhaoeusn',False)
