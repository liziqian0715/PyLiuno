import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter as Interpreter

class BuiltinTests(unittest.TestCase):
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

    def test_len_builtin(self):
        code = (
            "print(len([1,2,3]))\n"
            "print(len({'a':1,'b':2}))\n"
        )
        out = self.run_and_capture(code)
        lines = [l.strip() for l in out.strip().splitlines()]
        self.assertEqual(lines, ['3', '2'])

    def test_enumerate_in_for(self):
        code = (
            "for p in enumerate(['a','b'], 1):\n"
            "    print(p[0], p[1])\n"
        )
        out = self.run_and_capture(code)
        lines = [l.strip() for l in out.strip().splitlines()]
        self.assertEqual(lines, ['1 a', '2 b'])

if __name__ == '__main__':
    unittest.main()
