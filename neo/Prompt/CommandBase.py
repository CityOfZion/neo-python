from abc import ABC, abstractmethod
from neo.Prompt.Utils import get_arg
from typing import List


class ParameterDesc():
    def __init__(self, name, description, optional=False):
        self.name = name
        self.description = description
        self.optional = optional

    def __repr__(self):
        if self.optional:
            return f"{self.name:<15} - (Optional) {self.description}"
        else:
            return f"{self.name:<15} - {self.description}"

    def formatted_name(self):
        if self.optional:
            return f"({self.name})"
        else:
            return f"{{{self.name}}}"


class CommandDesc():
    def __init__(self, command, short_help, help, params: List[ParameterDesc] = None):
        """
        Command descriptor

        Args:
            command: 1 word command identifier
            short_help: short description of the purpose of the command
            help: '???'
            params: list of parameter descriptions belonging to the command
        """
        self.command = command  # command string
        self.short_help = short_help  # Short description of the command
        self.help = help  # Complete help text with details
        self.params = params if params else []

    def __repr__(self):
        s = self.command
        if self.short_help:
            s += f" # {self.short_help}"
        return s


class CommandBase(ABC):
    def __init__(self):
        super().__init__()
        self.__sub_commands = dict()

    @abstractmethod
    def execute(self, arguments):
        pass

    @abstractmethod
    def command_desc(self):
        pass

    # Raise KeyError exception if the command does not exist
    def execute_sub_command(self, id, arguments):
        self.__sub_commands[id].execute(arguments)

    # ids: can be either a string or a list of strings.
    def register_sub_command(self, ids, sub_command):
        if isinstance(ids, list):
            for id in ids:
                self.__register_sub_command(id, sub_command)
        else:
            self.__register_sub_command(ids, sub_command)

    def __register_sub_command(self, id, sub_command):
        if id in self.__sub_commands:
            raise ValueError(f"{id} is already a subcommand.")

        self.__sub_commands[id] = sub_command

    def command_descs_with_sub_commands(self):
        return [self.command_desc()] + [sub_cmd.command_desc() for sub_cmd in self.__sub_commands.values()]

    def __print_absolute_cmd_help(self, cmd):
        print(f"\n{cmd.command_desc().short_help.capitalize()}")
        params = ""
        for p in cmd.command_desc().params:
            params += f"{p.formatted_name()} "
        print(f"\nUsage: {cmd.command_desc().command} {params}\n")

        for p in cmd.command_desc().params:
            print(p)

    def handle_help(self, arguments):
        item = get_arg(arguments)
        if item == 'help':
            if len(self.__sub_commands) > 0:
                # show overview of subcommands and their purpose
                print(f"\nUsage: {self.command_desc().command} COMMAND\n")
                print(f"{self.command_desc().short_help.capitalize()}\n")
                print("Commands:")

                # Use a set to avoid duplicated lines.
                cmd_text = {
                    f"   {sub_cmd.command_desc().command:<15} - {sub_cmd.command_desc().short_help}"
                    for sub_cmd in self.__sub_commands.values()
                }

                for txt in cmd_text:
                    print(txt)
                print(f"\nRun '{self.command_desc().command} COMMAND help' for more information on the command.")
            else:
                self.__print_absolute_cmd_help(self)
        else:
            if arguments[-1] == 'help':
                if item in self.__sub_commands:
                    sub_cmd = self.__sub_commands[item]  # type: SubCommandBase
                    self.__print_absolute_cmd_help(sub_cmd)
                else:
                    print('Unknown command')


class SubCommandBase(CommandBase):

    @classmethod
    @abstractmethod
    def execute(cls, arguments):
        pass

    @abstractmethod
    def command_desc(self):
        pass
