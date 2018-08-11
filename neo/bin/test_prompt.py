from unittest import TestCase
import pexpect


class PromptTest(TestCase):

    def test_prompt_run(self):

        child = pexpect.spawn('np-prompt')
        index = child.expect(["neo", pexpect.EOF, pexpect.TIMEOUT])

        if index == 0:
            print('np-prompt running as expected')
        elif index == 1:
            print('np-prompt experienced an unexpected EOF')
        elif index == 2:
            print('np-prompt experienced an unexpected TIMEOUT')
        elif index != 0 and index != 1 and index != 2:
            print('test failed')

        self.assertEqual(index, 0)
        child.terminate()

    def test_prompt_open_wallet(self):

        child = pexpect.spawn('np-prompt')
        child.sendline('open wallet fixtures/testwallet.db3')
        child.sendline('testpassword')
        index = child.expect(['Opened wallet at fixtures/testwallet.db3'])

        if index == 0:
            print('Opened testwallet.db3 successfully')
        elif index != 0:
            print('test failed')

        self.assertEqual(index, 0)
        child.terminate()
