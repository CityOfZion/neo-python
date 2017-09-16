from unittest import TestCase


from boa.boa import Compiler


class CompileImportsTestCase(TestCase):

    def test_good(self):

        compiler = Compiler.Instance().Load('./boa/tests/src/Math.py')

        self.assertIsNotNone(compiler)

    def test_nodes(self):
        compiler = Compiler.Instance().Load('./boa/tests/src/Math.py')

        self.assertEqual(3, len(compiler.Nodes))

    def test_bad(self):
        compiler = Compiler.Instance().Load('./boa/tests/src/MathBad.py')

        self.assertIsNone(compiler)
