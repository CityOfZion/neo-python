from unittest import TestCase
from neo.Prompt.InputParser import InputParser


class TestInputParser(TestCase):
    input_parser = InputParser()

    def test_simple_whitespace_separation(self):
        command, arguments = self.input_parser.parse_input("this is a simple test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["is", "a", "simple", "test"])

    def test_keeping_double_quoted_strings_together(self):
        command, arguments = self.input_parser.parse_input("this \"is a simple\" test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["\"is a simple\"", "test"])

    def test_keeping_single_quoted_strings_together(self):
        command, arguments = self.input_parser.parse_input("this 'is a simple' test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["'is a simple'", "test"])

    def test_keeping_bracket_elements_together(self):
        command, arguments = self.input_parser.parse_input("this [is a simple] test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["[is a simple]", "test"])

    def test_keeping_brackets_and_strings_together(self):
        command, arguments = self.input_parser.parse_input("this [is \"a simple\"] test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["[is \"a simple\"]", "test"])

    def test_unmatched_brackets(self):
        command, arguments = self.input_parser.parse_input("this [is \"a simple\" test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["[is", "\"a simple\"", "test"])

    def test_unmatched_single_quotes(self):
        command, arguments = self.input_parser.parse_input("this is 'a simple test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["is", "'a", "simple", "test"])

    def test_unmatched_double_quotes(self):
        command, arguments = self.input_parser.parse_input("this is \"a simple test")
        self.assertEqual(command, "this")
        self.assertEqual(arguments, ["is", "\"a", "simple", "test"])

    def test_python_bytearrays(self):
        command, arguments = self.input_parser.parse_input("testinvoke bytearray(b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)') b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5'")
        self.assertEqual(command, "testinvoke")
        self.assertEqual(arguments, ["bytearray(b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')", "b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5'"])

    def test_python_bytearrays_in_lists(self):
        command, arguments = self.input_parser.parse_input("testinvoke f8d448b227991cf07cb96a6f9c0322437f1599b9 transfer [bytearray(b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)'), bytearray(b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5'), 1000]")
        self.assertEqual(command, "testinvoke")
        self.assertEqual(arguments, ["f8d448b227991cf07cb96a6f9c0322437f1599b9", "transfer", "[bytearray(b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)'), bytearray(b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5'), 1000]"])
