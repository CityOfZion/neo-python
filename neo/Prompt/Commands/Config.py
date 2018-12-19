from prompt_toolkit import prompt
from neo.logging import log_manager
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.Utils import get_arg
from neo.Settings import settings
from neo.Network.NodeLeader import NodeLeader
import logging


class CommandConfig(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandConfigOutput())
        self.register_sub_command(CommandConfigSCEvents())
        self.register_sub_command(CommandConfigDebugNotify())
        self.register_sub_command(CommandConfigVMLog())
        self.register_sub_command(CommandConfigNodeRequests())

    def command_desc(self):
        return CommandDesc('config', 'configure internal settings')

    def execute(self, arguments):
        item = get_arg(arguments)

        if not item:
            print("run `%s help` to see supported queries" % self.command_desc().command)
            return

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return


class CommandConfigOutput(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments=None):
        return start_output_config()

    def command_desc(self):
        return CommandDesc('output', 'configure the log output level settings')


class CommandConfigSCEvents(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        c1 = get_arg(arguments)
        if c1 is not None:
            c1 = c1.lower()
            if c1 == 'on' or c1 == '1':
                settings.set_log_smart_contract_events(True)
                print("Smart contract event logging is now enabled")
                return c1
            elif c1 == 'off' or c1 == '0':
                settings.set_log_smart_contract_events(False)
                print("Smart contract event logging is now disabled")
                return c1
            else:
                print("Cannot configure log. Please specify on|off or 1|0")
                return
        else:
            print("Cannot configure log. Please specify on|off or 1|0")
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'either "on"|"off" or 1|0')
        return CommandDesc('sc-events', 'toggle printing smart contract events', [p1])


class CommandConfigDebugNotify(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        c1 = get_arg(arguments)
        if c1 is not None:
            c1 = c1.lower()
            if c1 == 'on' or c1 == '1':
                settings.set_emit_notify_events_on_sc_execution_error(True)
                print("Smart contract emit Notify events on execution failure is now enabled")
                return c1
            elif c1 == 'off' or c1 == '0':
                settings.set_emit_notify_events_on_sc_execution_error(False)
                print("Smart contract emit Notify events on execution failure is now disabled")
                return c1
            else:
                print("Cannot configure log. Please specify on|off or 1|0")
                return
        else:
            print("Cannot configure log. Please specify on|off or 1|0")
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'either "on"|"off" or 1|0')
        return CommandDesc('sc-debug-notify', 'toggle printing Notify events on execution failure', [p1])


class CommandConfigVMLog(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        c1 = get_arg(arguments)
        if c1 is not None:
            c1 = c1.lower()
            if c1 == 'on' or c1 == '1':
                settings.set_log_vm_instruction(True)
                print("VM instruction execution logging is now enabled")
                return c1
            elif c1 == 'off' or c1 == '0':
                settings.set_log_vm_instruction(False)
                print("VM instruction execution logging is now disabled")
                return c1
            else:
                print("Cannot configure VM instruction logging. Please specify on|off or 1|0")
                return
        else:
            print("Cannot configure VM instruction logging. Please specify on|off or 1|0")
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'either "on"|"off" or 1|0')
        return CommandDesc('vm-log', 'toggle VM instruction execution logging to file', [p1])


class CommandConfigNodeRequests(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) in [1, 2]:
            if len(arguments) == 2:
                try:
                    return NodeLeader.Instance().setBlockReqSizeAndMax(int(arguments[0]), int(arguments[1]))
                except ValueError:
                    print("invalid values. Please specify a block request part and max size for each node, like 30 and 1000")
                    return False
            elif len(arguments) == 1:
                return NodeLeader.Instance().setBlockReqSizeByName(arguments[0])
        else:
            print("Invalid number of arguments")
            return False

    def command_desc(self):
        p1 = ParameterDesc('block-size', 'a preset of "slow"/"normal"/"fast", or a specific block request size (max. 500) e.g. 250 ')
        p2 = ParameterDesc('queue-size', 'the maximum number of outstanding block requests')
        return CommandDesc('node-requests', 'configure block request settings', [p1, p2])


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

    # provide confirmation of new settings
    print("\n")
    print("New Output Levels:")
    new_settings = {}
    for component, logger in log_manager.loggers.items():
        component_name = component.replace(log_manager.root, "")
        current_level = logging.getLevelName(logger.handlers[0].level)
        new_settings["%s" % component_name] = current_level
        print("[{}] new: {}".format(component_name, current_level))
    return new_settings
