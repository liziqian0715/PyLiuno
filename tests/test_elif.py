import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter as Interpreter

class ElifTests(unittest.TestCase):
    def run_and_capture(self, code):
        tokens = list(core.tokenize(code))
        p = core.Parser(tokens)
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

    def test_if_elif_else(self):
        code = (
            "def f(x):\n"
            "    if x < 0:\n"
            "        print('neg')\n"
            "    elif x == 0:\n"
            "        print('zero')\n"
            "    else:\n"
            "        print('pos')\n"
            "\n"
            "f(-1)\n"
            "f(0)\n"
            "f(2)\n"
        )
        out = self.run_and_capture(code)
        lines = [l.strip() for l in out.strip().splitlines()]
        self.assertEqual(lines, ['neg', 'zero', 'pos'])

    def test_elifs_chain_without_else(self):
        code = (
            "def g(x):\n"
            "    if x == 1:\n"
            "        print('one')\n"
            "    elif x == 2:\n"
            "        print('two')\n"
            "\n"
            "g(1)\n"
            "g(2)\n"
            "g(3)\n"
        )
        out = self.run_and_capture(code)
        lines = [l.strip() for l in out.strip().splitlines()]
        self.assertEqual(lines, ['one', 'two'])

if __name__ == '__main__':
    unittest.main()
