from unittest import TestCase
from neo.Prompt.InputParser import InputParser


class TestInputParser(TestCase):
    input_parser = InputParser()

    def test_simple_whitespace_separation(self):
        command, arguments = self.input_parser.parse_input('this is a simple test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['is', 'a', 'simple', 'test'])

    def test_keeping_double_quoted_strings_together(self):
        command, arguments = self.input_parser.parse_input('this "is a simple" test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['"is a simple"', 'test'])

    def test_keeping_single_quoted_strings_together(self):
        command, arguments = self.input_parser.parse_input('this \'is a simple\' test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['\'is a simple\'', 'test'])

    def test_keeping_bracket_elements_together(self):
        command, arguments = self.input_parser.parse_input('this [is a simple] test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['[is a simple]', 'test'])

    def test_keeping_brackets_and_strings_together(self):
        command, arguments = self.input_parser.parse_input('this [is \'a simple\'] test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['[is \'a simple\']', 'test'])

    def test_unmatched_brackets(self):
        command, arguments = self.input_parser.parse_input('this [is \'a simple\' test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['[is', '\'a simple\'', 'test'])

    def test_unmatched_single_quotes(self):
        command, arguments = self.input_parser.parse_input('this is \'a simple test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['is', '\'a', 'simple', 'test'])

    def test_unmatched_double_quotes(self):
        command, arguments = self.input_parser.parse_input('this is "a simple test')
        self.assertEqual(command, 'this')
        self.assertEqual(arguments, ['is', '"a', 'simple', 'test'])
