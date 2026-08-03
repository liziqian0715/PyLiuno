
markdown
# 🐉 PyLiuno

**说中文的编程语言，错误提示再也不怕了。**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

PyLiuno 是一个用 Python 实现的、语法接近 Python 的中文友好编程语言。
拥有世界级的中文错误提示系统，让编程学习不再被英文报错劝退。

---

## 🚀 快速开始

### 安装（一行命令，需要 SSH）

```bash
pip install git+ssh://git@github.com/liziqian0715/PyLiuno.git
或克隆安装
bash
git clone git@github.com:liziqian0715/PyLiuno.git
cd PyLiuno
pip install -e .
运行
bash
# 交互式 REPL
pyl repl

# 切换到中文
:lang zh

# 写代码
print("你好，PyLiuno！")

# 运行文件
pyl run examples/hello.pyl
✨ 特色
特性	说明
🀄 中文错误提示	运行时和语法错误全中文 + 友好建议
🎯 精准指向	错误位置用 ^ 标注，一目了然
📊 12种排序算法	内置 + 性能对比 + 过程可视化
🔮 独有逻辑运算符	xor / nand / nor
🛡️ try/catch/always	比 Python 更直观的异常处理
🌐 中英文双语	:lang zh / :lang en 一键切换
📋 示例
基本语法
python
# 变量和运算
x = 10
y = 20
print(x + y)

# 条件和循环
if x > 5:
    print("大于5")
elif x > 0:
    print("正数")

for i in range(5):
    print(i)

# 函数
def add(a, b=1):
    return a + b
print(add(5))
数据结构
python
# 列表
lst = [1, 2, 3]
lst.append(4)
print(lst.pop())

# 字典
d = {"a": 1, "b": 2}
for k, v in d.items():
    print(k, v)

# 列表推导式
squares = [x*x for x in range(5)]
异常处理
python
try:
    x = 1 / 0
catch 除零错误:
    print("不能除以零！")
catch 所有错误:
    print("出错了")
always:
    print("结束")
排序算法对比
python
arr = [5, 2, 8, 1, 9, 3]
print(sort(arr, mode='quick'))
sort(arr, mode='benchmark')
📦 内置函数
函数	说明
print()	输出
input()	输入
len()	长度
range()	范围
str() / int() / float() / bool() / list()	类型转换
sum() / max() / min()	聚合
type()	类型名
enumerate()	枚举
sort()	12种排序算法
open() / read() / write()	文件操作
🎯 错误提示示例
python
>>> print(x)
名称错误: 名称 'x' 未定义。请检查变量名拼写或是否忘记赋值 (line 1)
    print(x)
          ^

>>> 1+1=
意外的符号: 等号 '=' 第1行第4列

>>> print(1+1=2)
函数调用中不能使用赋值 等号 '='，你可能想写 '=='？ 第1行第10列
📁 项目结构
text
PyLiuno/
├── PyLiuno/
│   ├── __init__.py
│   ├── lexer.py         # 词法分析
│   ├── parser.py        # 递归下降解析
│   ├── ast.py           # AST 节点
│   ├── interpreter.py   # 解释器
│   ├── cli.py           # 命令行
│   ├── settings.py      # 语言设置
│   └── i18n.json        # 国际化模板
├── examples/            # 示例程序
├── tests/               # 单元测试
├── pyproject.toml       # 打包配置
└── README.md
🔧 开发
bash
# 安装开发模式
pip install -e .

# 运行测试
python -m unittest discover -v PyLiuno/tests
⚠️ Windows 用户注意
中文乱码时请先执行：

bash
chcp 65001
pyl repl
📄 许可
MIT License

🌟 版本历史
版本	内容
v0.1.0	完整语言 + 中文错误提示
v0.2.0	多值return + global + 方法调用
v0.3.0	import + 12种sort + benchmark
v0.3.1	字符串自动拼接 + elif精准指向
v0.3.2	关键字参数
v0.3.3	列表推导式
v0.3.4	for解包迭代 + in/not in
v0.3.5	try/catch/always











markdown
# 🐉 PyLiuno

**A Chinese-friendly programming language. Error messages you can actually read.**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

PyLiuno is a Python-like language implemented in Python, featuring a world-class **localized error message system** with friendly suggestions and precise caret pointing.

---

## 🚀 Quick Start

```bash
pip install git+ssh://git@github.com/liziqian0715/PyLiuno.git
pyl repl
✨ Highlights
🀄 Full Chinese error messages with suggestions

🎯 Source line + ^ caret pointing

📊 12 built-in sort algorithms with benchmark mode

🔮 Custom operators: xor, nand, nor

🛡️ try/catch/always for intuitive error handling

🌐 Bilingual: :lang zh / :lang en

📋 Code Examples
python
# Variables & loops
for i in range(5):
    print(i)

# Functions with defaults & keyword args
def greet(name, times=1):
    for _ in range(times):
        print("Hello, " + name)
greet("PyLiuno", times=3)

# List comprehension
squares = [x*x for x in range(5)]

# For unpacking
d = {"a": 1, "b": 2}
for k, v in d.items():
    print(k, v)

# Error handling
try:
    x = 1 / 0
catch ZeroDivisionError:
    print("Cannot divide by zero!")
always:
    print("Done")
🎯 Error Messages
text
>>> print(x)
NameError: name 'x' is not defined (line 1)
    print(x)
          ^
📦 Built-in Functions
Function	Description
print input len range	Basic I/O
str int float bool list	Type conversion
sum max min type	Aggregation
enumerate	Enumeration
sort	12 algorithms with benchmark
open read write	File I/O
⚠️ Windows
If Chinese output is garbled, run chcp 65001 first.

🌟 Versions
v0.1.0 → v0.3.5: Core language, Chinese errors, imports, 12 sorts, list comprehension, try/catch, and more.
