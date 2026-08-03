from PyLiuno import tokenize, Parser
from PyLiuno.compiler import Compiler
from PyLiuno.interpreter import Interpreter
from PyLiuno.vm import VM as PyVM
from pyliuno_vm import VM as RustVM
from PyLiuno.rust_vm_adapter import adapt_instructions
import time
code=chr(34)*3+chr(34).join([chr(34),chr(34)])+chr(34)*3
exec(open(chr(34)+chr(34)).read())