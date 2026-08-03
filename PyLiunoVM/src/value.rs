use crate::vm2::Vm;
use std::collections::HashMap;
use std::fmt;

#[derive(Debug, Clone)]
pub enum Value {
    Int(i64),
    Float(f64),
    String(String),
    Bool(bool),
    List(Vec<Value>),
    Dict(HashMap<String, Value>),
    Function(Function),
    Builtin(fn(&mut Vm, Vec<Value>) -> Result<Value, String>),
    None,
}

#[derive(Debug, Clone)]
pub struct Function {
    pub name: String,
    pub params: Vec<String>,
    pub body: Vec<(String, Option<Value>)>,
    pub constants: Vec<Value>,
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Value::Int(n) => write!(f, "{}", n),
            Value::Float(n) => write!(f, "{}", n),
            Value::String(s) => write!(f, "{}", s),
            Value::Bool(b) => write!(f, "{}", b),
            Value::List(v) => write!(f, "{:?}", v),
            Value::Dict(d) => write!(f, "{:?}", d),
            Value::None => write!(f, "None"),
            _ => write!(f, "<function>"),
        }
    }
}