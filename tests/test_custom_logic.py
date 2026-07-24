import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Parser, Interpreter

class CustomLogicTests(unittest.TestCase):
    def run_and_capture(self, code):
        tokens = list(core.tokenize(code))
        p = Parser(tokens)
        mod = p.parse()
        interpreter = Interpreter()
        old_stdout = sys.stdout
        try:
            buf = io.StringIO()
            sys.stdout = buf
            interpreter.run_module(mod)
            return buf.getvalue()
        finally:
            sys.stdout = old_stdout

    def test_xor_truth(self):
        code = (
            "print(True xor False)\n"
            "print(True xor True)\n"
            "print(False xor False)\n"
        )
        out = self.run_and_capture(code)
        lines = [l.strip() for l in out.strip().splitlines()]
        self.assertEqual(lines, ['True', 'False', 'False'])

    def test_nand_truth_and_shortcircuit(self):
        code = (
            "def bad():\n"
            "    return 1/0\n"
            "print(True nand True)\n"
            "print(True nand False)\n"
            "print(False nand True)\n"
            # short-circuit: left False, bad() should not be called
            "print(False nand bad())\n"
        )
        out = self.run_and_capture(code)
        lines = [l.strip() for l in out.strip().splitlines()]
        self.assertEqual(lines, ['False', 'True', 'True', 'True'])

    def test_nor_truth_and_shortcircuit(self):
        code = (
            "def bad():\n"
            "    return 1/0\n"
            "print(False nor False)\n"
            "print(False nor True)\n"
            "print(True nor False)\n"
            # short-circuit: left True, bad() should not be called
            "print(True nor bad())\n"
        )
        out = self.run_and_capture(code)
        lines = [l.strip() for l in out.strip().splitlines()]
        self.assertEqual(lines, ['True', 'False', 'False', 'False'])

if __name__ == '__main__':
    unittest.main()
