import unittest
import PyLiuno as core

class ParserTests(unittest.TestCase):
    def test_assign_parsing(self):
        code = "x = 1\n"
        tokens = list(core.tokenize(code))
        p = core.Parser(tokens)
        mod = p.parse()
        # Expect Module with one Assign statement
        self.assertEqual(len(mod.body), 1)
        stmt = mod.body[0]
        self.assertEqual(type(stmt).__name__, 'Assign')
        self.assertEqual(stmt.target.id, 'x')
        self.assertEqual(type(stmt.value).__name__, 'Number')
        self.assertEqual(stmt.value.value, 1)

    def test_literal_name_nodes_have_col(self):
        code = "x = True\n"
        tokens = list(core.tokenize(code))
        p = core.Parser(tokens)
        mod = p.parse()
        stmt = mod.body[0]
        self.assertEqual(type(stmt).__name__, 'Assign')
        self.assertEqual(type(stmt.value).__name__, 'Name')
        self.assertTrue(hasattr(stmt.value, 'col'))
        self.assertEqual(stmt.value.col, 5)

    def test_funcdef_and_call_parsing(self):
        code = "def f(a):\n    return a\n\nf(2)\n"
        tokens = list(core.tokenize(code))
        p = core.Parser(tokens)
        mod = p.parse()
        # first node should be FuncDef, second ExprStmt(Call)
        self.assertGreaterEqual(len(mod.body), 2)
        self.assertEqual(type(mod.body[0]).__name__, 'FuncDef')
        self.assertEqual(mod.body[0].name, 'f')
        # check call
        call_stmt = mod.body[1]
        self.assertIn(type(call_stmt).__name__, ('ExprStmt', 'Expr'))
        # If ExprStmt, its expr should be Call
        if type(call_stmt).__name__ == 'ExprStmt':
            self.assertEqual(type(call_stmt.expr).__name__, 'Call')
        else:
            self.assertEqual(type(call_stmt).__name__, 'Call')

if __name__ == '__main__':
    unittest.main()
