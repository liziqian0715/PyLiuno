import unittest

import PyLiuno as core
from PyLiuno.parser import ParserError


class ErrorLocalizationTests(unittest.TestCase):
    def test_lexer_unexpected_character_localized_zh(self):
        original_lang = core.settings.LANGUAGE
        try:
            core.settings.set_language('zh')
            with self.assertRaises(SyntaxError) as cm:
                list(core.tokenize('1+1@\n'))
            msg = str(cm.exception)
            self.assertIn("意外的字符: @", msg)
            self.assertIn('第1行', msg)
        finally:
            core.settings.set_language(original_lang)

    def test_parser_unexpected_token_localized_zh(self):
        original_lang = core.settings.LANGUAGE
        try:
            core.settings.set_language('zh')
            tokens = list(core.tokenize('1+1=\n'))
            with self.assertRaises(ParserError) as cm:
                core.Parser(tokens).parse()
            msg = str(cm.exception)
            self.assertIn('意外的符号:', msg)
            self.assertIn("等号 '='", msg)
            self.assertIn('第1行第4列', msg)
        finally:
            core.settings.set_language(original_lang)

    def test_print_unexpected_token_in_call_localized_zh(self):
        original_lang = core.settings.LANGUAGE
        try:
            core.settings.set_language('zh')
            tokens = list(core.tokenize('print(1+1=\n'))
            with self.assertRaises(ParserError) as cm:
                core.Parser(tokens).parse()
            msg = str(cm.exception)
            self.assertIn('意外的符号:', msg)
            self.assertIn("等号 '='", msg)
            self.assertIn('第1行第10列', msg)
        finally:
            core.settings.set_language(original_lang)

    def test_key_error_localized_zh_preserves_format(self):
        original_lang = core.settings.LANGUAGE
        try:
            core.settings.set_language('zh')
            code = "def f():\n    d = {'x': 1}\n    print(d['y'])\nf()\n"
            tokens = list(core.tokenize(code))
            p = core.Parser(tokens)
            mod = p.parse()
            interpreter = core.Interpreter(source_code=code)
            with self.assertRaises(KeyError) as cm:
                interpreter.run_module(mod)
            msg = str(cm.exception)
            self.assertIn('键错误:', msg)
            self.assertTrue(msg.startswith('键错误:'))
            self.assertIn("print(d['y'])", msg)
            self.assertIn('line 3', msg)
            self.assertNotIn('\\n', msg)
        finally:
            core.settings.set_language(original_lang)

    def test_type_error_common_message_localized_zh(self):
        original_lang = core.settings.LANGUAGE
        try:
            core.settings.set_language('zh')
            code = "def f():\n    a = 'x' + 1\nf()\n"
            tokens = list(core.tokenize(code))
            p = core.Parser(tokens)
            mod = p.parse()
            interpreter = core.Interpreter(source_code=code)
            with self.assertRaises(TypeError) as cm:
                interpreter.run_module(mod)
            msg = str(cm.exception)
            self.assertIn('类型错误:', msg)
            self.assertIn('只能将字符串', msg)
            self.assertIn('line 2', msg)
            self.assertNotIn('can only concatenate str', msg)
        finally:
            core.settings.set_language(original_lang)


if __name__ == '__main__':
    unittest.main()
