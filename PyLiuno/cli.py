"""CLI entrypoint for PyLiuno

Commands:
  pyl run <file>   - run a PyLiuno source file
  pyl repl         - start a simple REPL (end multi-line input with an empty line)
  pyl -h           - show help
"""
import sys
import io
import os
from typing import List
from . import tokenize, Parser, Interpreter
from .settings import set_language
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers import PythonLexer
from prompt_toolkit.formatted_text import HTML


# 修复 Windows 终端中文乱码
if sys.platform == 'win32':
    try:
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    except Exception:
        pass
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass


PROMPT = 'PyLiuno> '
ANSI_GRAY = '\x1b[90m'
ANSI_RESET = '\x1b[0m'


def run_file(path: str):
    
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    tokens = tokenize(code)
    parser = Parser(tokens, source_code=code)
    try:
        mod = parser.parse()
    except Exception as e:
        # ParserError 消息已按当前语言格式化，直接打印
        print('Error:', e)
        return
    interp = Interpreter(source_code=code)
    try:
        interp.run_module(mod)
    except Exception as e:
        # run_module 已经做了本地化，直接打印
        print('Error:', e)


def repl():
    print('PyLiuno REPL (enter blank line to evaluate, Ctrl-D to exit)')
    interp = Interpreter()
    buffer_lines: List[str] = []
    indent_level = 0
    INDENT_STR = '    '
    
    session = PromptSession()
    style = Style.from_dict({
        'pygments.keyword': "#c974e2",
        'pygments.literal.string': "#89c379",
        'pygments.number': '#d19a66',
        'pygments.comment': '#5c6370 italic',
        'pygments.name.function': "#619aef",
        'pygments.name.builtin': '#e5c07b',
        'pygments.name': '#abb2bf',           # 普通变量名（白色）
        'pygments.operator': '#56b6c2',
    })
    
    try:
        while True:
            try:
                if indent_level == 0:
                    prompt = PROMPT
                else:
                    spaces = ' ' * (len(PROMPT) + indent_level * len(INDENT_STR) - 4)
                    prompt = HTML(f'<ansigray>... </ansigray>{spaces}')
                
                line = session.prompt(
                    prompt,
                    lexer=PygmentsLexer(PythonLexer),
                    style=style,
                    include_default_pygments_style=False,
                )
            except (EOFError, KeyboardInterrupt):
                print()
                break

            # :lang command to switch language
            parts = line.strip().split()
            if parts and parts[0].lower() == ':lang':
                if len(parts) >= 2:
                    lang = parts[1]
                    try:
                        set_language(lang)
                        if lang.lower() == 'zh':
                            print('语言已切换为中文')
                        else:
                            print(f'Language set to {lang}')
                    except Exception as e:
                        print('Error:', e)
                else:
                    print('Usage: :lang en|zh')
                continue

            # Blank line handling
            if line.strip() == '':
                if indent_level > 0:
                    indent_level -= 1
                    continue
                code = '\n'.join(buffer_lines).strip()
                buffer_lines = []
                if not code:
                    continue
                try:
                    tokens = tokenize(code)
                    parser = Parser(tokens, source_code=code)
                    mod = parser.parse()
                    interp.source_code = code
                    interp.run_module(mod)
                except Exception as e:
                    print('Error:', e)
                continue

            if indent_level > 0:
                line = INDENT_STR * indent_level + line
            buffer_lines.append(line)

            if line.rstrip().endswith(':'):
                indent_level += 1

    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')


def usage():
    print('Usage: pyl run <file> | pyl repl')


def main(argv: List[str] = None):
    if argv is None:
        argv = sys.argv[1:]
    # 支持 --lang zh/en 参数
    if '--lang' in argv:
        idx = argv.index('--lang')
        if idx + 1 < len(argv):
            set_language(argv[idx + 1])
            argv = argv[:idx] + argv[idx+2:]
    if not argv:
        usage(); return 1
    cmd = argv[0]
    if cmd == 'run' and len(argv) >= 2:
        run_file(argv[1]); return 0
    if cmd == 'repl':
        repl(); return 0
    if cmd in ('-h', '--help'):
        usage(); return 0
    print(f'Unknown command: {cmd}')
    usage()
    return 2


if __name__ == '__main__':
    sys.exit(main())
