# -*- coding:utf-8 -*-
"""
Description:
    Exceptions
Usage:
    from AntShares.Exceptions import *
"""


class WorkIdError(Exception):
    """Work Id Error"""
    def __init__(self, info):
        super(Exception, self).__init__(info)
        self.error_code = 0x0002

class OutputError(Exception):
    """Output Error"""
    def __init__(self, info):
        super(Exception, self).__init__(info)
        self.error_code = 0x0003

class RegisterNameError(Exception):
    """Regiser Transaction Name Error"""
    def __init__(self, info):
        super(Exception, self).__init__(info)
        self.error_code = 0x0004
