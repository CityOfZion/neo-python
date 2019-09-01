from pyparsing import ZeroOrMore, Regex


class InputParser:
    parser = ZeroOrMore(Regex(r'\[[^]]*\]') | Regex(r'"[^"]*"') | Regex(r'\'[^\']*\'') | Regex(r'[^ ]+'))

    def parse_input(self, user_input):
        if len(user_input):
            command_parts = self.parser.parseString(user_input)
            command_parts = merge_items(command_parts)
            return command_parts[0], command_parts[1:]
        return None, None


def merge_items(command_parts):
    s = 0
    f = 0
    for n, i in enumerate(command_parts):
        for x in i:
            if x == '[':
                s += 1
            if x == ']':
                f += 1
        if s != f:
            try:
                command_parts[n] = command_parts[n] + " " + command_parts[n + 1]
                command_parts.pop(n + 1)
                merge_items(command_parts)
            except IndexError:
                pass
    return command_parts
