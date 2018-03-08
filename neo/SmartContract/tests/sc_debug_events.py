"""
 Sample smart contract for use in `test_sc_debug_events.py`
"""
from boa.interop.Neo.Runtime import Notify, Log


def Main(args):
    Notify("Start main")
    x = args[0]
    Log(x)
    Notify("End main")
