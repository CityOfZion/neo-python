from pyparsing import ZeroOrMore, Regex


class InputParser(object):
    parser = ZeroOrMore(Regex(r'\[[^]]*\]') | Regex(r'"[^"]*"') | Regex(r'\'[^\']*\'') | Regex(r'[^ ]+'))

    def parse_input(self, user_input):
        if len(user_input):
            command_parts = self.parser.parseString(user_input)
            return command_parts[0], command_parts[1:]
        return None, None
