import unittest
import io
import sys
import PyLiuno as core
from PyLiuno import Interpreter as Interpreter

class InterpreterTests(unittest.TestCase):
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

    def test_arithmetic_and_print(self):
        code = "x = 2\ny = x + 3\nprint(y)\n"
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '5')

    def test_factorial(self):
        code = (
            "def fact(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    else:\n"
            "        return n * fact(n - 1)\n"
            "\n"
            "print(fact(5))\n"
        )
        out = self.run_and_capture(code)
        self.assertEqual(out.strip(), '120')

    def test_for_loop_runtime_error_location(self):
        code = "for i in range(5):\n    a = a + 1\n"
        tokens = list(core.tokenize(code))
        p = core.Parser(tokens)
        mod = p.parse()
        interpreter = Interpreter(source_code=code)
        with self.assertRaises(NameError) as cm:
            interpreter.run_module(mod)
        msg = str(cm.exception)
        self.assertIn('line 2', msg)
        self.assertIn('    a = a + 1', msg)
        self.assertIn('^', msg)

if __name__ == '__main__':
    unittest.main()
