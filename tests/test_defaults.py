import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter

class DefaultParamTests(unittest.TestCase):
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

    def test_simple_default(self):
        code = "def f(a, b=1):\n    print(a, b)\n\nf(5)\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '5 1')

    def test_override_default(self):
        code = "def f(a, b=1):\n    print(a, b)\n\nf(5, 2)\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '5 2')

    def test_all_defaults(self):
        code = "def g(a=10, b=20):\n    print(a, b)\n\ng()\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '10 20')

if __name__ == '__main__':
    unittest.main()
