from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from neo.UserPreferences import preferences
import os
import sys

token_style = Style.from_dict({
    "command": preferences.token_style['Command'],
    "neo": preferences.token_style['Neo'],
    "default": preferences.token_style['Default'],
    "number": preferences.token_style['Number'],
})


class PromptPrinter():
    def __init__(self):
        self.printer = self._internal_prompt_print

    def reset_printer(self):
        self.printer = self._internal_prompt_print

    def _internal_prompt_print(self, *args, **kwargs):

        kwargs['sep'] = kwargs.pop('sep', ' ')
        kwargs['end'] = kwargs.pop('end', '\n')
        kwargs['file'] = kwargs.pop('file', sys.stdout)
        kwargs['style'] = token_style
        frags = []
        for a in args:
            if isinstance(a, FormattedText):
                frags.append(a)
            else:
                frags.append(FormattedText([("class:command", str(a))]))

        print_formatted_text(*frags, **kwargs)

    def print(self, *args, **kwargs):
        if 'NEOPYTHON_UNITTEST' in os.environ:
            print(*args, **kwargs)
        else:
            self.printer(*args, **kwargs)


pp = PromptPrinter()


def prompt_print(*args, **kwargs):
    pp.print(*args, **kwargs)
