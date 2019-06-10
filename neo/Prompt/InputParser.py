from pyparsing import ZeroOrMore, Regex


class InputParser:
    parser = ZeroOrMore(Regex(r'\[[^]]*\]') | Regex(r'"[^"]*"') | Regex(r'\'[^\']*\'') | Regex(r'[^ ]+'))

    def parse_input(self, user_input):
        if len(user_input):
            command_parts = self.parser.parseString(user_input)
            for n, i in enumerate(command_parts):
                for x in i:
                    if x != ']':
                        break
                    command_parts[n - 1] = command_parts[n - 1] + i
                    command_parts.pop(n)
                    break
            return command_parts[0], command_parts[1:]
        return None, None
