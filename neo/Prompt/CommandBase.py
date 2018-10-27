from abc import ABC, abstractmethod


class CommandDesc():
    def __init__(self, command, short_help=None, help=None):
        self.command = command  # command string
        self.short_help = short_help  # Short description of the command
        self.help = help  # Complete help text with details

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


class SubCommandBase():

    @classmethod
    @abstractmethod
    def execute(cls, arguments):
        pass

    @abstractmethod
    def command_desc(self):
        pass
