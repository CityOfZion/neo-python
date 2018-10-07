from unittest import TestCase
from unittest.case import _BaseTestCaseContext
import logging
import collections
from neo.logging import log_manager


class _CapturingHandler(logging.Handler):
    """
    A logging handler capturing all (raw and formatted) logging output.
    """

    def __init__(self):
        logging.Handler.__init__(self)
        _LoggingWatcher = collections.namedtuple("_LoggingWatcher",
                                                 ["records", "output"])

        self.watcher = _LoggingWatcher([], [])

    def flush(self):
        pass

    def emit(self, record):
        self.watcher.records.append(record)
        msg = self.format(record)
        self.watcher.output.append(msg)


class _AssertLogHandlerContext(_BaseTestCaseContext):
    def __init__(self, test_case, component_name, level):
        _BaseTestCaseContext.__init__(self, test_case)
        self.component_name = component_name
        self.level = level
        self._logger = log_manager.getLogger(self.component_name)

    def __enter__(self):
        LOGGING_FORMAT = "%(levelname)s:%(name)s:%(message)s"

        # save original handler
        self.stdio_handler = self._logger.handlers[0]

        # replace with our capture handler
        capture_handler = _CapturingHandler()
        capture_handler.setLevel(self.level)
        capture_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
        self._logger.handlers[0] = capture_handler
        self._logger.addHandler(capture_handler)

        return capture_handler.watcher

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            # let unexpected exceptions pass through
            return False

        # restore original handler
        self._logger.handlers[0] = self.stdio_handler


class NeoTestCase(TestCase):
    def assertLogHandler(self, component_name: str, level: int):
        """
        This method must be used as a context manager, and will yield
        a recording object with two attributes: `output` and `records`.
        At the end of the context manager, the `output` attribute will
        be a list of the matching formatted log messages of the stdio handler
        and the `records` attribute will be a list of the corresponding LogRecord
        objects.

        Args:
            component_name: the component we want to capture logs of i.e. vm or network
            level: the logging level to capture at i.e. DEBUG, INFO, ERROR

        Returns:
            context manager
        """
        return _AssertLogHandlerContext(self, component_name, level)
