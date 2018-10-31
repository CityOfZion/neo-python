from prompt_toolkit import prompt
from neo.logging import log_manager
import logging


def start_output_config():
    # temporarily mute stdout while we try to reconfigure our settings
    # components like `network` set at DEBUG level will spam through the console
    # making it impractical to configure output levels
    log_manager.mute_stdio()

    print("Select your desired configuration per component.")
    print("(1) DEBUG (2) INFO (3) ERROR (enter) keep current")
    print("")

    configurations = []
    level_conversion = {1: logging.DEBUG, 2: logging.INFO, 3: logging.ERROR}

    # cycle through all known components
    for component, logger in log_manager.loggers.items():
        component_name = component.replace(log_manager.root, "")
        current_level = logging.getLevelName(logger.handlers[0].level)
        line = "[{}] current: {} new: ".format(component_name, current_level)

        choice = None
        try:
            choice = int(prompt(line))
        except ValueError:
            pass

        # invalid choice or enter == keep current
        if not choice:
            continue

        new_log_level = level_conversion.get(choice, logging.NOTSET)
        if new_log_level != logging.NOTSET:
            configurations.append((component_name, new_log_level))

    # finally apply new settings
    if configurations:
        log_manager.config_stdio(configurations)

    # and re-enable stdio
    log_manager.unmute_stdio()
