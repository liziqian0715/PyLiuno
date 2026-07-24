import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter

class BreakContinueTests(unittest.TestCase):
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

    def test_break_in_for(self):
        code = "a=[1,2,3,4]\ns=0\nfor x in a:\n    if x==3:\n        break\n    s = s + x\nprint(s)\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '3')

    def test_continue_in_for(self):
        code = "a=[1,2,3,4]\ns=0\nfor x in a:\n    if x==2:\n        continue\n    s = s + x\nprint(s)\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '8')

    def test_break_in_while(self):
        code = "i=0\ns=0\nwhile i<5:\n    i = i + 1\n    if i==3:\n        break\n    s = s + i\nprint(s)\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '3')

    def test_continue_in_while(self):
        code = "i=0\ns=0\nwhile i<5:\n    i = i + 1\n    if i==2:\n        continue\n    s = s + i\nprint(s)\n"
        out = self.run_and_capture(code)
        # i increments before check; when i==2 it continues (skip adding 2)
        # Final printed s should be 1+3+4+5 = 13
        self.assertEqual(out.strip(), '13')

if __name__ == '__main__':
    unittest.main()
