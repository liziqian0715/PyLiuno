import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter

class ForTests(unittest.TestCase):
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

    def test_for_over_list(self):
        code = "a = [1,2,3]\ns = 0\nfor x in a:\n    s = s + x\nprint(s)\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '6')

    def test_for_over_dict(self):
        code = "d = {'a':1, 'b':2}\nfor k in d:\n    print(k)\n"
        out = self.run_and_capture(code)
        # dict preserves insertion order
        self.assertEqual(out.strip(), 'a\nb')

if __name__ == '__main__':
    unittest.main()
