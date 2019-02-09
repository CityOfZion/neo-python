from prompt_toolkit import prompt
from neo.logging import log_manager
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.Utils import get_arg
from neo.Settings import settings
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.PromptPrinter import prompt_print as print
from distutils import util
import logging


class CommandConfig(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandConfigOutput())
        self.register_sub_command(CommandConfigSCEvents())
        self.register_sub_command(CommandConfigDebugNotify())
        self.register_sub_command(CommandConfigVMLog())
        self.register_sub_command(CommandConfigNodeRequests())
        self.register_sub_command(CommandConfigMaxpeers())
        self.register_sub_command(CommandConfigNEP8())

    def command_desc(self):
        return CommandDesc('config', 'configure internal settings')

    def execute(self, arguments):
        item = get_arg(arguments)

        if not item:
            print(f"run `{self.command_desc().command} help` to see supported queries")
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
        if len(arguments) == 0:
            print("Please specify the required parameter")
            return False

        try:
            flag = bool(util.strtobool(arguments[0]))
            settings.set_log_smart_contract_events(flag)
        except ValueError:
            print("Invalid option")
            return False

        if flag:
            print("Smart contract event logging is now enabled")
            return True
        else:
            print("Smart contract event logging is now disabled")
            return True

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'either "on"|"off" or 1|0')
        return CommandDesc('sc-events', 'toggle printing smart contract events', [p1])


class CommandConfigDebugNotify(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) == 0:
            print("Please specify the required parameter")
            return False

        try:
            flag = bool(util.strtobool(arguments[0]))
            settings.set_emit_notify_events_on_sc_execution_error(flag)
        except ValueError:
            print("Invalid option")
            return False

        if flag:
            print("Smart contract emit Notify events on execution failure is now enabled")
            return True
        else:
            print("Smart contract emit Notify events on execution failure is now disabled")
            return True

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'either "on"|"off" or 1|0')
        return CommandDesc('sc-debug-notify', 'toggle printing smart contract Notify events on execution failure', [p1])


class CommandConfigVMLog(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) == 0:
            print("Please specify the required parameter")
            return False

        try:
            flag = bool(util.strtobool(arguments[0]))
            settings.set_log_vm_instruction(flag)
        except ValueError:
            print("Invalid option")
            return False

        if flag:
            print("VM instruction execution logging is now enabled")
            return True
        else:
            print("VM instruction execution logging is now disabled")
            return True

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
                    print("Invalid values. Please specify a block request part and max size for each node, like 30 and 1000")
                    return False
            elif len(arguments) == 1:
                return NodeLeader.Instance().setBlockReqSizeByName(arguments[0])
        else:
            print("Please specify the required parameter")
            return False

    def command_desc(self):
        p1 = ParameterDesc('block-size', 'preset of "slow"/"normal"/"fast", or a specific block request size (max. 500) e.g. 250 ')
        p2 = ParameterDesc('queue-size', 'maximum number of outstanding block requests')
        return CommandDesc('node-requests', 'configure block request settings', [p1, p2])

    def handle_help(self, arguments):
        super().handle_help(arguments)
        print(f"\nCurrent settings {self.command_desc().params[0].name}:"
              f" {NodeLeader.Instance().BREQPART} {self.command_desc().params[1].name}: {NodeLeader.Instance().BREQMAX}")


class CommandConfigNEP8(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        try:
            flag = bool(util.strtobool(arguments[0]))
        except ValueError:
            print("Invalid option")
            return False

        settings.COMPILER_NEP_8 = flag
        if flag:
            print("NEP-8 compiler instruction usage is ON")
        else:
            print("NEP-8 compiler instruction usage is OFF")

        return True

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'either "on"|"off" or 1|0')
        return CommandDesc('nep8', 'toggle using NEP-8 compiler instructions', [p1])


class CommandConfigMaxpeers(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        c1 = get_arg(arguments)
        if c1 is not None:
            try:
                current_max = settings.CONNECTED_PEER_MAX
                settings.set_max_peers(c1)
                c1 = int(c1)
                p_len = len(NodeLeader.Instance().Peers)
                if c1 < current_max and c1 < p_len:
                    to_remove = p_len - c1
                    peers = NodeLeader.Instance().Peers
                    for i in range(to_remove):
                        peer = peers[-1]  # disconnect last peer added first
                        peer.Disconnect("Max connected peers reached", isDead=False)
                        peers.pop()

                print(f"Maxpeers set to {c1}")
                return c1
            except ValueError:
                print("Please supply a positive integer for maxpeers")
                return
        else:
            print(f"Maintaining maxpeers at {settings.CONNECTED_PEER_MAX}")
            return

    def command_desc(self):
        p1 = ParameterDesc('number', 'maximum number of nodes to connect to')
        return CommandDesc('maxpeers', 'configure number of max peers', [p1])


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
    print("\nNew Output Levels:")
    new_settings = {}
    for component, logger in log_manager.loggers.items():
        component_name = component.replace(log_manager.root, "")
        current_level = logging.getLevelName(logger.handlers[0].level)
        new_settings["%s" % component_name] = current_level
        print("[{}] new: {}".format(component_name, current_level))
    return new_settings
