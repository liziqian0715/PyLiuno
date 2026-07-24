import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter

class DictTests(unittest.TestCase):
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

    def test_dict_literal_and_key_access(self):
        code = "d = {'a': 1, 'b': 2}\nprint(d['a'])\nprint(d['b'])\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '1\n2')

if __name__ == '__main__':
    unittest.main()
