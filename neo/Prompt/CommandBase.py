from abc import ABC, abstractmethod
from neo.Prompt.Utils import get_arg
from typing import List
from neo.Prompt.PromptPrinter import prompt_print as print


class ParameterDesc():
    def __init__(self, name, description, optional=False):
        """
        Parameter descriptor

        Args:
            name: 1 word parameter identifier.
            description: short description of the purpose of the parameter. What does it configure/do.
            optional: flag indicating whether the parameter is optional. Defaults to mandatory (false).
        """
        self.name = name
        self.description = description
        self.optional = optional

    def __repr__(self):
        return self.to_str()

    def to_str(self, ljust_len=15):
        if self.optional:
            return f"{self.name.ljust(ljust_len)} - (Optional) {self.description}"
        else:
            return f"{self.name.ljust(ljust_len)} - {self.description}"

    def formatted_name(self):
        if self.optional:
            return f"({self.name})"
        else:
            return f"{{{self.name}}}"


class CommandDesc():
    def __init__(self, command, short_help, params: List[ParameterDesc] = None):
        """
        Command descriptor

        Args:
            command: 1 word command identifier
            short_help: short description of the purpose of the command
            params: list of parameter descriptions belonging to the command
        """
        self.command = command
        self.short_help = short_help
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
        self.__parent_command = None
        self.__additional_ids = set()

    @abstractmethod
    def execute(self, arguments):
        pass

    @abstractmethod
    def command_desc(self):
        pass

    # Raise KeyError exception if the command does not exist
    def execute_sub_command(self, id, arguments):
        return self.__sub_commands[id].execute(arguments)

    def register_sub_command(self, sub_command, additional_ids=[]):
        """
        Register a command as a subcommand.
        It will have it's CommandDesc.command string used as id. Additional ids can be provided.

        Args:
            sub_command (CommandBase): Subcommand to register.
            additional_ids (List[str]): List of additional ids. Can be empty.
        """
        self.__register_sub_command(sub_command, sub_command.command_desc().command)
        self.__additional_ids.update(additional_ids)
        for id in additional_ids:
            self.__register_sub_command(sub_command, id)

    def __register_sub_command(self, sub_command, id):
        if id in self.__sub_commands:
            raise ValueError(f"{id} is already a subcommand of {self.command_desc().command}.")
        if sub_command.__parent_command and sub_command.__parent_command != self:
            raise ValueError(f"The given sub_command is already a subcommand of another command ({sub_command.__parent_command.command_desc().command}.")

        self.__sub_commands[id] = sub_command
        sub_command.__parent_command = self

    # Include subcommands recursively.
    def command_descs_with_sub_commands(self):
        sub_descs = [
            desc
            for sub_cmd in self.__sub_commands.values()
            for desc in sub_cmd.command_descs_with_sub_commands()
        ]
        return [self.command_desc()] + sub_descs

    def __print_absolute_cmd_help(self):
        print(f"\n{self.command_desc().short_help.capitalize()}")
        params = ""
        for p in self.command_desc().params:
            params += f"{p.formatted_name()} "
        print(f"\nUsage: {self.__command_with_parents()} {params}\n")

        if len(self.command_desc().params) > 0:
            min_indent = 15
            longest_param_name = max(min_indent, max(len(p.name) for p in self.command_desc().params))
            for p in self.command_desc().params:
                print(p.to_str(longest_param_name))

    def __command_with_parents(self):
        s = self.command_desc().command
        if self.__parent_command:
            s = self.__parent_command.__command_with_parents() + " " + s
        return s

    def _usage_str(self):
        return f"Usage: {self.__command_with_parents()} COMMAND"

    def handle_help(self, arguments):
        item = get_arg(arguments)
        if item == 'help':
            if len(self.__sub_commands) > 0:
                # show overview of subcommands and their purpose
                print(f"\n{self._usage_str()}\n")
                print(f"{self.command_desc().short_help.capitalize()}\n")
                print("Commands:")

                # print commands in alphabetic order
                for k in sorted(self.__sub_commands.keys()):
                    if k not in self.__additional_ids:
                        print(f"   {self.__sub_commands[k].command_desc().command:<15} - {self.__sub_commands[k].command_desc().short_help}")

                print(f"\nRun '{self.__command_with_parents()} COMMAND help' for more information on the command.")
            else:
                self.__print_absolute_cmd_help()
        else:
            if arguments[-1] == 'help':
                if item in self.__sub_commands:
                    self.__sub_commands[item].handle_help(arguments[1:])
                else:
                    print('Unknown command')
