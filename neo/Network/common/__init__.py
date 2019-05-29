import asyncio
import string
from neo.Network.common.events import Events
from contextlib import contextmanager

from prompt_toolkit.eventloop import set_event_loop as prompt_toolkit_set_event_loop
from prompt_toolkit.eventloop import create_asyncio_event_loop as prompt_toolkit_create_async_event_loop
from prompt_toolkit import prompt

msgrouter = Events()


def wait_for(coro):
    with get_event_loop() as loop:
        return loop.run_until_complete(coro)


def blocking_prompt(text, **kwargs):
    with get_event_loop() as loop:
        return loop.run_until_complete(prompt(text, async_=True, **kwargs))


class LoopPool:
    def __init__(self):
        self.loops = set()

    def borrow_loop(self):
        try:
            return self.loops.pop()
        except KeyError:
            return asyncio.new_event_loop()

    def return_loop(self, loop):
        # loop.stop()
        self.loops.add(loop)


loop_pool = LoopPool()


@contextmanager
def get_event_loop():
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        yield loop
    else:
        new_loop = loop_pool.borrow_loop()
        asyncio.set_event_loop(new_loop)
        prompt_loop = loop_pool.borrow_loop()
        new_prompt_loop = prompt_toolkit_create_async_event_loop(new_loop)
        prompt_toolkit_set_event_loop(new_prompt_loop)
        running_loop = asyncio.events._get_running_loop()
        asyncio.events._set_running_loop(None)
        try:
            yield new_loop
        finally:
            loop_pool.return_loop(new_loop)
            loop_pool.return_loop(prompt_loop)
            asyncio.set_event_loop(loop)
            prompt_toolkit_set_event_loop(prompt_toolkit_create_async_event_loop(loop))
            asyncio.events._set_running_loop(running_loop)


chars = string.digits + string.ascii_letters
base = len(chars)


def encode_base62(num: int):
    """Encode number in base62, returns a string."""
    if num < 0:
        raise ValueError('cannot encode negative numbers')

    if num == 0:
        return chars[0]

    digits = []
    while num:
        rem = num % base
        num = num // base
        digits.append(chars[rem])
    return ''.join(reversed(digits))
