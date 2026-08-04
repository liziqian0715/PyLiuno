use std::collections::HashMap;
use crate::value::Value;

pub struct Vm {
    pub stack: Vec<Value>,
    pub variables: Vec<HashMap<String, Value>>,
    pub constants: Vec<Value>,
    pub ip: usize,
    pub builtins: HashMap<String, fn(&mut Vm, Vec<Value>) -> Result<Value, String>>,
}

impl Vm {
    pub fn new() -> Self {
        let mut vm = Vm {
            stack: Vec::new(),
            variables: vec![HashMap::new()],
            constants: Vec::new(),
            ip: 0,
            builtins: HashMap::new(),
        };
        vm.register_builtins();
        vm
    }

    fn register_builtins(&mut self) {
        self.builtins.insert("print".to_string(), |vm, args| {
            for arg in &args {
                print!("{} ", arg);
            }
            println!();
            Ok(Value::None)
        });
    }

    pub fn run(&mut self, instructions: &[(String, Option<Value>)], constants: &[Value]) -> Result<(), String> {
        self.constants = constants.to_vec();
        self.ip = 0;

        while self.ip < instructions.len() {
            let (ref opcode, ref operand) = instructions[self.ip];
            self.ip += 1;

            match opcode.as_str() {
                "LOAD_CONST" => {
                    let val = match operand {
                        Some(Value::Int(idx)) => self.constants.get(*idx as usize).cloned().unwrap_or(Value::None),
                        Some(v) => v.clone(),
                        None => Value::None,
                    };
                    self.stack.push(val);
                }
                "STORE_NAME" => {
                    let name = match operand {
                        Some(Value::String(s)) => s.clone(),
                        _ => return Err("STORE_NAME needs string".into()),
                    };
                    let val = self.stack.pop().unwrap_or(Value::None);
                    let frame = self.variables.last_mut().unwrap();
                    frame.insert(name, val);
                }
                "LOAD_NAME" => {
                    let name = match operand {
                        Some(Value::String(s)) => s.clone(),
                        _ => return Err("LOAD_NAME needs string".into()),
                    };
                    let val = self.resolve_name(&name)?;
                    self.stack.push(val);
                }
                "BINARY_ADD" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    let result = match (a, b) {
                        (Value::Int(a), Value::Int(b)) => Value::Int(a + b),
                        (Value::Float(a), Value::Float(b)) => Value::Float(a + b),
                        (Value::String(a), Value::String(b)) => Value::String(a + &b),
                        (a, b) => Value::String(format!("{}{}", a, b)),
                    };
                    self.stack.push(result);
                }
                "BINARY_SUB" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Int(a - b));
                    }
                }
                "BINARY_MUL" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Int(a * b));
                    }
                }
                "BINARY_DIV" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(1));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Int(a / b));
                    }
                }
                "BINARY_IN" => {
                    let b = self.stack.pop().unwrap_or(Value::None);
                    let a = self.stack.pop().unwrap_or(Value::None);
                    match &b {
                        Value::List(items) => self.stack.push(Value::Bool(items.contains(&a))),
                        Value::Dict(d) => self.stack.push(Value::Bool(d.contains_key(&format!("{}", a)))),
                        _ => self.stack.push(Value::Bool(false)),
                    }
                }
                "BINARY_OR" => {
                    let b = self.stack.pop().unwrap_or(Value::Bool(false));
                    let a = self.stack.pop().unwrap_or(Value::Bool(false));
                    self.stack.push(Value::Bool(is_truthy(&a) || is_truthy(&b)));
                }
                "BINARY_NOR" => {
                    let b = self.stack.pop().unwrap_or(Value::Bool(false));
                    let a = self.stack.pop().unwrap_or(Value::Bool(false));
                    self.stack.push(Value::Bool(!(is_truthy(&a) || is_truthy(&b))));
                }
                "BINARY_XOR" => {
                    let b = self.stack.pop().unwrap_or(Value::Bool(false));
                    let a = self.stack.pop().unwrap_or(Value::Bool(false));
                    self.stack.push(Value::Bool(is_truthy(&a) != is_truthy(&b)));
                }
                "BINARY_AND" => {
                    let b = self.stack.pop().unwrap_or(Value::Bool(false));
                    let a = self.stack.pop().unwrap_or(Value::Bool(false));
                    self.stack.push(Value::Bool(is_truthy(&a) && is_truthy(&b)));
                }
                "BINARY_NAND" => {
                    let b = self.stack.pop().unwrap_or(Value::Bool(false));
                    let a = self.stack.pop().unwrap_or(Value::Bool(false));
                    self.stack.push(Value::Bool(!(is_truthy(&a) && is_truthy(&b))));
                }
                "UNARY_NOT" => {
                    let a = self.stack.pop().unwrap_or(Value::Bool(false));
                    self.stack.push(Value::Bool(!is_truthy(&a)));
                }

                "JUMP_BACKWARD" => {
                    let jump = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("JUMP_BACKWARD needs int".into()),
                    };
                    self.ip = jump;
                }
                "COMPARE_EQ" => {
                    let b = self.stack.pop().unwrap_or(Value::None);
                    let a = self.stack.pop().unwrap_or(Value::None);
                    self.stack.push(Value::Bool(a == b));
                }
                "COMPARE_NE" => {
                    let b = self.stack.pop().unwrap_or(Value::None);
                    let a = self.stack.pop().unwrap_or(Value::None);
                    self.stack.push(Value::Bool(a != b));
                }
                "COMPARE_LT" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Bool(a < b));
                    } else {
                        self.stack.push(Value::Bool(false));
                    }
                }
                "COMPARE_GT" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Bool(a > b));
                    } else {
                        self.stack.push(Value::Bool(false));
                    }
                }
                "COMPARE_LE" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Bool(a <= b));
                    } else {
                        self.stack.push(Value::Bool(false));
                    }
                }
                "COMPARE_GE" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Bool(a >= b));
                    } else {
                        self.stack.push(Value::Bool(false));
                    }
                }
                "JUMP_IF_FALSE" => {
                    let jump = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("JUMP_IF_FALSE needs int".into()),
                    };
                    let val = self.stack.pop().unwrap_or(Value::Bool(true));
                    if is_falsey(&val) {
                        self.ip = jump;
                    }
                }
                "JUMP_FORWARD" => {
                    let jump = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("JUMP_FORWARD needs int".into()),
                    };
                    self.ip = jump;
                }
                "GET_ITER" => {
                    // 栈顶是列表，替换为迭代器状态: [列表, 当前索引]
                    let obj = self.stack.pop().unwrap_or(Value::List(vec![]));
                    match obj {
                        Value::List(items) => {
                            self.stack.push(Value::List(items));
                            self.stack.push(Value::Int(0));
                        }
                        _ => return Err(format!("Cannot iterate over {:?}", obj)),
                    }
                }
                "FOR_ITER" => {
                    let jump = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("FOR_ITER needs int".into()),
                    };
                    // 栈: [..., 列表, 索引]
                    let idx = self.stack.pop().unwrap_or(Value::Int(-1));
                    let idx = match idx {
                        Value::Int(i) => i,
                        _ => return Err("Expected int index".into()),
                    };
                    // peek 列表
                    let list = self.stack.last().cloned().unwrap_or(Value::List(vec![]));
                    match list {
                        Value::List(ref items) => {
                            if idx >= items.len() as i64 {
                                // 迭代结束，弹出列表，跳转
                                self.stack.pop();
                                self.ip = jump;
                            } else {
                                // 还有元素
                                let item = items[idx as usize].clone();
                                // 恢复状态: 列表, 新索引
                                self.stack.push(Value::Int(idx + 1));
                                // 当前元素放栈顶给 STORE_NAME
                                self.stack.push(item);
                            }
                        }
                        _ => return Err("Expected list in FOR_ITER".into()),
                    }
                }
                "CALL_FUNCTION" => {
                    let arg_count = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("CALL_FUNCTION needs int".into()),
                    };

                    let mut args = Vec::new();
                    for _ in 0..arg_count {
                        args.push(self.stack.pop().unwrap_or(Value::None));
                    }
                    args.reverse();
                    let func = self.stack.pop().unwrap_or(Value::None);
                    match func {
                        Value::Function(f) => {
                            // 补全缺失参数
                            while args.len() < f.params.len() {
                                args.push(Value::Int(0));
                            }
                            // 创建新帧
                            let mut new_frame = self.variables.last().cloned().unwrap_or_default();
                            for (i, param) in f.params.iter().enumerate() {
                                let val = args.get(i).cloned().unwrap_or(Value::None);
                                new_frame.insert(param.clone(), val);
                            }
                            self.variables.push(new_frame);
                            // 执行函数体
                            let old_ip = self.ip;
                            self.ip = 0;
                            let result = match self.run(&f.body, &f.constants) {
                                Ok(()) => {
                                    // 函数执行完，栈顶是返回值
                                    self.stack.pop().unwrap_or(Value::None)
                                }
                                Err(e) => return Err(e),
                            };
                            self.ip = old_ip;
                            self.variables.pop();
                            self.stack.push(result);
                        }
                        Value::Builtin(b) => {
                            b(self, args)?;
                        }
                        Value::String(name) => {
                            // 从变量表查找
                            let f = self.resolve_name(&name)?;
                            match f {
                                Value::Function(f) => {
                            // 补全缺失参数
                            while args.len() < f.params.len() {
                                args.push(Value::Int(0));
                            }
                            // 创建新帧
                            let mut new_frame = self.variables.last().cloned().unwrap_or_default();
                            for (i, param) in f.params.iter().enumerate() {
                                let val = args.get(i).cloned().unwrap_or(Value::None);
                                new_frame.insert(param.clone(), val);
                            }
                                    self.variables.push(new_frame);
                                    let old_ip = self.ip;
                                    self.ip = 0;
                                    let result = match self.run(&f.body, &f.constants) {
                                        Ok(()) => self.stack.pop().unwrap_or(Value::None),
                                        Err(e) => return Err(e),
                                    };
                                    self.ip = old_ip;
                                    self.variables.pop();
                                    self.stack.push(result);
                                }
                                _ => return Err(format!("{} is not callable", name)),
                            }
                        }
                        _ => return Err(format!("{:?} is not callable", func)),
                    }
                }
                "BUILD_DICT" => {
                    let count = match operand { Some(Value::Int(i)) => *i as usize, _ => return Err("BUILD_DICT needs int".into()) };
                    let mut dict = HashMap::new();
                    for _ in 0..count {
                        let v = self.stack.pop().unwrap_or(Value::None);
                        let k = self.stack.pop().unwrap_or(Value::None);
                        dict.insert(format!("{}", k), v);
                    }
                    self.stack.push(Value::Dict(dict));
                }
                "BINARY_NOT_IN" => {
                    let b = self.stack.pop().unwrap_or(Value::None);
                    let a = self.stack.pop().unwrap_or(Value::None);
                    match &b {
                        Value::List(items) => self.stack.push(Value::Bool(!items.contains(&a))),
                        Value::Dict(d) => self.stack.push(Value::Bool(!d.contains_key(&format!("{}", a)))),
                        _ => self.stack.push(Value::Bool(true)),
                    }
                }
                "BINARY_SUBSCR" => {
                    let idx = self.stack.pop().unwrap_or(Value::Int(0));
                    let obj = self.stack.pop().unwrap_or(Value::None);
                    let result = match (&obj, &idx) {
                        (Value::List(items), Value::Int(i)) => items.get(*i as usize).cloned().unwrap_or(Value::None),
                        (Value::Dict(d), key) => d.get(&format!("{}", key)).cloned().unwrap_or(Value::None),
                        (Value::String(s), Value::Int(i)) => {
                            let chars: Vec<char> = s.chars().collect();
                            if (*i as usize) < chars.len() {
                                Value::String(chars[*i as usize].to_string())
                            } else { Value::None }
                        }
                        _ => Value::None,
                    };
                    self.stack.push(result);
                }
                "BINARY_MOD" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(1));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Int(a % b));
                    }
                }
                "BUILD_LIST" => {
                    let count = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("BUILD_LIST needs int".into()),
                    };
                    let mut items = Vec::new();
                    for _ in 0..count {
                        items.push(self.stack.pop().unwrap_or(Value::None));
                    }
                    items.reverse();
                    self.stack.push(Value::List(items));
                }
                "BUILD_LIST_COMP" => {
                    let var = match operand { Some(Value::String(s)) => s.clone(), _ => return Err("needs var".into()) };
                    // 栈: [expr_result, iterable]
                    let iter_val = self.stack.pop().unwrap_or(Value::List(vec![]));
                    let expr_val = self.stack.pop().unwrap_or(Value::None);
                    match iter_val {
                        Value::List(items) => {
                            let mut result = Vec::new();
                            for item in &items {
                                let frame = self.variables.last_mut().unwrap();
                                frame.insert(var.clone(), item.clone());
                                // 执行表达式——这里需要重新执行 expr，但 expr 只算了一次
                                // 简化：直接复制 expr_val 的值
                                result.push(expr_val.clone());
                            }
                            self.stack.push(Value::List(result));
                        }
                        _ => return Err("Expected list".into()),
                    }
                }
                "RETURN_VALUE" => {
                    return Ok(());
                }
                "PRINT" => {
                    let val = self.stack.pop().unwrap_or(Value::None);
                    println!("{}", val);
                }
                "BREAK_LOOP" => {
                    // 跳出最内层循环：找到对应的 JUMP_FORWARD 或循环结束位置
                    // 简化：跳过当前循环体剩余指令
                    self.ip = instructions.len(); // 跳到末尾
                }
                "CONTINUE_LOOP" => {
                    // 跳到循环开始
                    // 简化：什么都不做
                }
                "METHOD_CALL" => {
                    
                    let arg_count = match operand { Some(Value::Int(i)) => *i as usize, _ => 0 };
                    let mut args = Vec::new();
                    for i in 0..arg_count {
                        let a = self.stack.pop().unwrap_or(Value::None);
                        args.push(a);
                    }
                    args.reverse();
                    let method_name = match self.stack.pop() {
                        Some(Value::String(s)) => s,
                        Some(v) => return Err(format!("Expected method name, got {:?}", v)),
                        None => return Err("Empty stack".into()),
                    };
                    let obj = self.stack.pop().unwrap_or(Value::None);
                    let result = match (&obj, method_name.as_str()) {
                        (Value::List(items), "append") => {
                            let mut new_items = items.clone();
                            new_items.push(args.into_iter().next().unwrap_or(Value::None));
                            Value::List(new_items)
                        }
                        (Value::List(items), "pop") => {
                            let mut new_items = items.clone();
                            let val = new_items.pop().unwrap_or(Value::None);
                            self.stack.push(val);
                            Value::List(new_items)
                        }
                        other => return Err(format!("No method: {:?}", other)),
                    };
                    self.stack.push(result);
                }
                "POP_TOP" => { self.stack.pop(); }
                "STORE_GLOBAL" => {
                    let name = match operand { Some(Value::String(s)) => s.clone(), _ => return Err("STORE_GLOBAL needs string".into()) };
                    let val = self.stack.pop().unwrap_or(Value::None);
                    self.variables[0].insert(name, val);
                }
                _ => return Err(format!("Unknown opcode: {}", opcode)),
            }
        }
        Ok(())
    }

    fn resolve_name(&self, name: &str) -> Result<Value, String> {
        if let Some(func) = self.builtins.get(name) {
            return Ok(Value::Builtin(*func));
        }
        for frame in self.variables.iter().rev() {
            if let Some(val) = frame.get(name) {
                return Ok(val.clone());
            }
        }
        Err(format!("name '{}' is not defined", name))
    }
}

fn matches_eq(a: &Value, b: &Value) -> bool {
    match (a, b) {
        (Value::Int(a), Value::Int(b)) => a == b,
        (Value::String(a), Value::String(b)) => a == b,
        (Value::Bool(a), Value::Bool(b)) => a == b,
        _ => false,
    }
}

fn is_falsey(v: &Value) -> bool {
    match v {
        Value::Bool(false) | Value::None => true,
        Value::Int(0) => true,
        _ => false,
    }
}

fn is_truthy(v: &Value) -> bool {
    match v {
        Value::Bool(false) | Value::None => false,
        Value::Int(0) => false,
        Value::String(s) if s.is_empty() => false,
        Value::List(items) if items.is_empty() => false,
        _ => true,
    }
}