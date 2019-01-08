"""
    Logging happens all throughout neo-python at various verbosity levels (INFO, DEBUG etc) and in different components (e.g. network, db, vm)

    The LogManager class in this module is setup to allow for the following:
    - turn logging on or off for independent components
    - set independent logging levels for components (e.g. network at INFO, vm at DEBUG)
    - filter component logs shown in the CLI/GUI while keeping all log levels when logging to e.g. a file


    The LogManager class by default creates a logger at log level DEBUG with a `StreamHandler` (stdio) at log level INFO. The net effect is that
    stdout will only show INFO and above, whereas if you choose to add another handler e.g. a FileLogger it will have DEBUG and above information.


    By default getting a logger `log_manager.getLogger()` will give you a `logging.Logger` class of name `neo-python.generic`.
    When specifying a component name e.g. `getLogger('db')` you'll get `neo-python.db`. This allows you to integrate neo-python and process
    its logs via the parent id `neo-python`.


    Filtering of component output is achieved by varying the levels on the `StreamHandler` of a logger, not on the Logger class itself.
    This choice leaves room for applying `Filters` (see https://docs.python.org/3/library/logging.html#filter-objects)
    for more fine grained control within components if the future requires this.

    The LogManager class only has convenience methods for adjusting levels on the attached `StreamHandler`, not for the loggers itself for
    the earlier mentioned reasons.

    Example usage:
        from neo.logging import log_manager

        logger = log_manager.getLogger()
        logger.info("I log for generic components like the prompt or Util classes")

        network_logger = log_manager.getLogger('network')
        logger.info("I log for network classes like NodeLeader and NeoNode")

        # since network classes can be very active and verbose, we might want to raise the level to just show ERROR or above
        logconfig = ('network', logging.ERROR) # a tuple of (`component name`, `log level`)
        log_manager.config_stdio([logconfig]) # takes a list of log configurations

"""

import logging
from typing import List, Optional, Tuple
from logzero import LogFormatter

Component = str
LogLevel = int
LogConfiguration = Tuple[Component, LogLevel]


class BlockAll(logging.Filter):
    def filter(self, record):
        # allow no records to pass through
        return False


class LogManager(object):
    loggers: dict = {}

    root = 'neo-python.'

    block_all_filter = BlockAll()

    def config_stdio(self, log_configurations: Optional[List[LogConfiguration]] = None, default_level=logging.INFO) -> None:
        """
        Configure the stdio `StreamHandler` levels on the specified loggers.
        If no log configurations are specified then the `default_level` will be applied to all handlers.

        Args:
            log_configurations: a list of (component name, log level) tuples
            default_level: logging level to apply when no log_configurations are specified
        """
        # no configuration specified, apply `default_level` to the stdio handler of all known loggers
        if not log_configurations:
            for logger in self.loggers.values():
                self._restrict_output(logger, default_level)
        # only apply specified configuration to the stdio `StreamHandler` of the specific component
        else:
            for component, level in log_configurations:
                try:
                    logger = self.loggers[self.root + component]
                except KeyError:
                    raise ValueError("Failed to configure component. Invalid name: {}".format(component))
                self._restrict_output(logger, level)

    def _restrict_output(self, logger: logging.Logger, level: int) -> None:
        # we assume the first handler is always our STDIO handler
        if logger.hasHandlers():
            logger.handlers[0].setLevel(level)

    def mute_stdio(self) -> None:
        """
        Intended to temporarily mute messages by applying a `BlockAll` filter.
        Use in combination with `unmute_stdio()`
        """

        # The benefit of using a Filter here for disabling messages is that we do not have to restore old logging levels.
        for logger in self.loggers.values():
            if logger.hasHandlers():
                logger.handlers[0].addFilter(self.block_all_filter)

    def unmute_stdio(self) -> None:
        """
        Intended to re-store the temporarily disabled logging of `mute_stdio()` by removing the `BlockAll` filter.
        """
        for logger in self.loggers.values():
            if logger.hasHandlers():
                logger.handlers[0].removeFilter(self.block_all_filter)

    def getLogger(self, component_name: str = None) -> logging.Logger:
        """
        Get the logger instance matching ``component_name`` or create a new one if non-existent.

        Args:
            component_name: a neo-python component name. e.g. network, vm, db

        Returns:
            a logger for the specified component.
        """
        logger_name = self.root + (component_name if component_name else 'generic')
        _logger = self.loggers.get(logger_name)
        if not _logger:
            _logger = logging.getLogger(logger_name)

            stdio_handler = logging.StreamHandler()
            stdio_handler.setFormatter(LogFormatter())
            stdio_handler.setLevel(logging.INFO)
            _logger.addHandler(stdio_handler)
            _logger.setLevel(logging.DEBUG)
            self.loggers[logger_name] = _logger
        return _logger


log_manager = LogManager()
