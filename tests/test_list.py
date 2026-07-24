import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter

class ListTests(unittest.TestCase):
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

    def test_list_literal_and_index(self):
        code = "a = [1, 2, 3]\nprint(a[0])\nprint(a[2])\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '1\n3')

if __name__ == '__main__':
    unittest.main()
