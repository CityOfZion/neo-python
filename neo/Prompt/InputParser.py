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
    start = 0
    finish = 0
    for i, part in enumerate(command_parts):
        for x in part:
            if x == '[':
                start += 1
            if x == ']':
                finish += 1
        if start != finish:
            try:
                command_parts[i] = command_parts[i] + " " + command_parts[i + 1]
                command_parts.pop(i + 1)
                merge_items(command_parts)
            except IndexError:
                pass
    return command_parts
