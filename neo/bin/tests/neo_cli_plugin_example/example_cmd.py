from neo.Prompt.CommandBase import CommandBase, CommandDesc


class ExampleCmd(CommandBase):

    def __init__(self):
        super().__init__()
        self._isGroupBaseCommand = True

    def execute(self, arguments):
        pass

    def command_desc(self):
        return CommandDesc('unittest_cmd', 'does nothing but validate plugin loading')

    def execute_sub_command(self, id, arguments):
        return super().execute_sub_command(id, arguments)

    def register_sub_command(self, sub_command, additional_ids=[]):
        super().register_sub_command(sub_command, additional_ids)

    def command_descs_with_sub_commands(self):
        return super().command_descs_with_sub_commands()

    def handle_help(self, arguments):
        super().handle_help(arguments)
