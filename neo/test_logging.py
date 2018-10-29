from neo.Utils.NeoTestCase import NeoTestCase
from neo.logging import log_manager
import logging


class LogManagerTestCase(NeoTestCase):
    def test_default_level_info(self):
        """
        Make sure the the logger instance
        """
        with self.assertLogHandler('generic', level=logging.INFO) as context:
            logger = log_manager.getLogger()

            logger.info("generic info")
            logger.debug("generic debug")
            logger.error("generic error")

            # we should not see 3 generic logger outputs
            self.assertNotEqual(len(context.output), 3)
            # we should only should see 2 generic logger outputs
            self.assertEqual(len(context.output), 2)
            # we should not see 'DEBUG' outputs
            self.assertNotIn('DEBUG:', context.output)

    def test_disable_specific_component(self):
        with self.assertLogHandler('generic', level=logging.INFO) as generic_context:
            with self.assertLogHandler('db', level=logging.INFO) as db_context:
                generic_logger = log_manager.getLogger()
                db_logger = log_manager.getLogger('db')

                # we first write some input
                generic_logger.info("generic info")
                db_logger.info("db info")

                # and assert success
                self.assertEqual(len(generic_context.output), 1)
                self.assertEqual(len(db_context.output), 1)

                # we disable the generic component
                log_manager.config_stdio([('generic', logging.ERROR)])

                # write something on both loggers
                generic_logger.info("generic info")
                db_logger.info("db info")

                # `generic` should not have any additional output since it was disabled
                self.assertEqual(len(generic_context.output), 1)
                # `db` should have 1 additional output
                self.assertEqual(len(db_context.output), 2)

    def test_disable_all_components_via_config(self):
        with self.assertLogHandler('generic', level=logging.INFO) as generic_context:
            with self.assertLogHandler('db', level=logging.INFO) as db_context:
                generic_logger = log_manager.getLogger()
                db_logger = log_manager.getLogger('db')

                # we trigger some logging
                generic_logger.info("generic info")
                db_logger.info("db info")

                # now disable
                log_manager.config_stdio(default_level=logging.ERROR)

                # trigger some more
                generic_logger.info("generic info")
                db_logger.info("db info")

                # make sure no additional records have been added
                self.assertEqual(len(generic_context.output), 1)
                self.assertEqual(len(db_context.output), 1)

    def test_individual_level_per_component(self):
        def count_in(needle, stack):
            return sum(map(lambda item: needle in item, stack))

        with self.assertLogHandler('generic', level=logging.INFO) as generic_context:
            with self.assertLogHandler('db', level=logging.INFO) as db_context:
                generic_logger = log_manager.getLogger()
                db_logger = log_manager.getLogger('db')

                # default logging is INFO, we now set it to DEBUG for all components
                log_manager.config_stdio(default_level=logging.DEBUG)

                generic_logger.info("generic info")
                generic_logger.debug("generic debug")
                db_logger.info("db info")
                db_logger.debug("db debug")

                self.assertEqual(2, len(generic_context.output))
                self.assertEqual(1, count_in("INFO", generic_context.output))
                self.assertEqual(1, count_in("DEBUG", generic_context.output))
                self.assertEqual(2, len(db_context.output))
                self.assertEqual(1, count_in("INFO", db_context.output))
                self.assertEqual(1, count_in("DEBUG", db_context.output))

                # now we switch one component to a different level
                log_manager.config_stdio([('db', logging.INFO)])

                generic_logger.info("generic info")
                generic_logger.debug("generic debug")
                db_logger.info("db info")
                db_logger.debug("db debug")

                # `generic` should have 2 new items (INFO + DEBUG)
                self.assertEqual(4, len(generic_context.output))
                self.assertEqual(2, count_in("INFO", generic_context.output))
                self.assertEqual(2, count_in("DEBUG", generic_context.output))

                # `db` should have only 1 new item (INFO)
                self.assertEqual(3, len(db_context.output))
                self.assertEqual(2, count_in("INFO", db_context.output))
                self.assertEqual(1, count_in("DEBUG", db_context.output))

    def test_configuring_non_existing_component(self):
        with self.assertRaises(ValueError) as context:
            log_manager.config_stdio([("fake_component", logging.ERROR)])
        self.assertIn("Failed to configure component. Invalid name", str(context.exception))

    def test_mute_and_unmute_stdio(self):
        with self.assertLogHandler('generic', level=logging.DEBUG) as generic_context:
            with self.assertLogHandler('network', level=logging.DEBUG) as network_context:
                generic_logger = log_manager.getLogger()
                network_logger = log_manager.getLogger('network')

                generic_logger.debug("debug")
                generic_logger.info("info")
                generic_logger.error("error")
                generic_logger.critical("critical")

                # also log on non-default loggers to make sure we hit all components
                network_logger.debug("network debug")
                # we normally 'disable' logging in `neo-python` by raising the level to `ERROR`
                # for mute we want no messages at all, so logging at critical should have no result either.
                network_logger.critical("network critical")

                # make sure we initially have working output
                self.assertEqual(4, len(generic_context.output))
                self.assertEqual(2, len(network_context.output))

                # now mute all
                log_manager.mute_stdio()

                generic_logger.debug("debug")
                generic_logger.info("info")
                generic_logger.error("error")
                generic_logger.critical("critical")

                network_logger.debug("network debug")
                network_logger.critical("network critical")

                # no records should have been added
                self.assertEqual(4, len(generic_context.output))
                self.assertEqual(2, len(network_context.output))

                # now unmute all
                log_manager.unmute_stdio()

                generic_logger.debug("debug")
                generic_logger.info("info")
                generic_logger.error("error")
                generic_logger.critical("critical")

                network_logger.debug("network debug")
                network_logger.critical("network critical")

                # new records should now have been added again
                self.assertEqual(8, len(generic_context.output))
                self.assertEqual(4, len(network_context.output))
