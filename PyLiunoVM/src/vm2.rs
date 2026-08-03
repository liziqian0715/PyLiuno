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
                    let idx = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("LOAD_CONST needs int".into()),
                    };
                    let val = self.constants[idx].clone();
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
                "COMPARE_EQ" => {
                    let b = self.stack.pop().unwrap_or(Value::None);
                    let a = self.stack.pop().unwrap_or(Value::None);
                    self.stack.push(Value::Bool(matches_eq(&a, &b)));
                }
                "COMPARE_LT" => {
                    let b = self.stack.pop().unwrap_or(Value::Int(0));
                    let a = self.stack.pop().unwrap_or(Value::Int(0));
                    if let (Value::Int(a), Value::Int(b)) = (&a, &b) {
                        self.stack.push(Value::Bool(a < b));
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
                "JUMP_BACKWARD" => {
                    let jump = match operand {
                        Some(Value::Int(i)) => *i as usize,
                        _ => return Err("JUMP_BACKWARD needs int".into()),
                    };
                    self.ip = jump;
                }
                "PRINT" => {
                    let val = self.stack.pop().unwrap_or(Value::None);
                    println!("{}", val);
                }
                "POP_TOP" => { self.stack.pop(); }
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