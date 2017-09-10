from unittest import TestCase


from boa.Compiler import Compiler


class CompileImportsTestCase(TestCase):



    def test_good(self):

        compiler = Compiler.Compile('./boa/sources/Math.py')

        self.assertIsNotNone(compiler)

    def test_nodes(self):
        compiler = Compiler.Compile('./boa/sources/Math.py')


        self.assertEqual(3, len(compiler.Nodes))


    def test_bad(self):
        compiler = Compiler.Compile('./boa/sources/MathBad.py')

        self.assertIsNone(compiler)