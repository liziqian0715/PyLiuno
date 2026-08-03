use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict, PyTuple};
use std::collections::HashMap;

#[pyclass]
struct VM {
    stack: Vec<PyObject>,
    variables: HashMap<String, PyObject>,
    constants: Vec<PyObject>,
    ip: usize,
}

#[pymethods]
impl VM {
    #[new]
    fn new() -> Self {
        VM {
            stack: Vec::new(),
            variables: HashMap::new(),
            constants: Vec::new(),
            ip: 0,
        }
    }

    fn run(&mut self, py: Python, instructions: Vec<(String, Option<PyObject>)>, constants: Vec<PyObject>) -> PyResult<()> {
        self.constants = constants;
        self.ip = 0;

        while self.ip < instructions.len() {
            let (ref opcode, ref operand) = instructions[self.ip];
            self.ip += 1;

            match opcode.as_str() {
                "LOAD_CONST" => {
                    let idx: usize = operand.as_ref().unwrap().extract(py)?;
                    let val = self.constants[idx].clone_ref(py);
                    self.stack.push(val);
                }
                "LOAD_NAME" => {
                    let name: String = operand.as_ref().unwrap().extract(py)?;
                    if let Some(val) = self.variables.get(&name) {
                        self.stack.push(val.clone_ref(py));
                    } else {
                        return Err(pyo3::exceptions::PyNameError::new_err(format!("name '{}' is not defined", name)));
                    }
                }
                "STORE_NAME" => {
                    let name: String = operand.as_ref().unwrap().extract(py)?;
                    let val = self.stack.pop().unwrap();
                    self.variables.insert(name, val);
                }
                "BINARY_ADD" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__add__", (b,))?;
                    self.stack.push(result);
                }
                "BINARY_SUB" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__sub__", (b,))?;
                    self.stack.push(result);
                }
                "BINARY_MUL" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__mul__", (b,))?;
                    self.stack.push(result);
                }
                "BINARY_DIV" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__truediv__", (b,))?;
                    self.stack.push(result);
                }
                "BINARY_MOD" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__mod__", (b,))?;
                    self.stack.push(result);
                }
                "BINARY_SUBSCR" => {
                    let idx = self.stack.pop().unwrap();
                    let obj = self.stack.pop().unwrap();
                    let result = obj.call_method1(py, "__getitem__", (idx,))?;
                    self.stack.push(result);
                }
                "BINARY_IN" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = b.call_method1(py, "__contains__", (a,))?;
                    self.stack.push(result);
                }
                "BINARY_NOT_IN" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = b.call_method1(py, "__contains__", (a,))?;
                    let not_result = result.call_method0(py, "__invert__")?;
                    self.stack.push(not_result);
                }
                "BUILD_LIST" => {
                    let count: usize = operand.as_ref().unwrap().extract(py)?;
                    let mut items = Vec::new();
                    for _ in 0..count {
                        items.push(self.stack.pop().unwrap());
                    }
                    items.reverse();
                    let list = PyList::new(py, items)?;
                    self.stack.push(list.into());
                }
                "BUILD_DICT" => {
                    let count: usize = operand.as_ref().unwrap().extract(py)?;
                    let dict = PyDict::new(py);
                    for _ in 0..count {
                        let v = self.stack.pop().unwrap();
                        let k = self.stack.pop().unwrap();
                        dict.set_item(k, v)?;
                    }
                    self.stack.push(dict.into());
                }
                "COMPARE_EQ" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__eq__", (b,))?;
                    self.stack.push(result);
                }
                "COMPARE_NE" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__ne__", (b,))?;
                    self.stack.push(result);
                }
                "COMPARE_LT" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__lt__", (b,))?;
                    self.stack.push(result);
                }
                "COMPARE_GT" => {
                    let b = self.stack.pop().unwrap();
                    let a = self.stack.pop().unwrap();
                    let result = a.call_method1(py, "__gt__", (b,))?;
                    self.stack.push(result);
                }
                "JUMP_IF_FALSE" => {
                    let jump_to: usize = operand.as_ref().unwrap().extract(py)?;
                    let val = self.stack.pop().unwrap();
                    let is_true: bool = val.extract(py)?;
                    if !is_true {
                        self.ip = jump_to;
                    }
                }
                "JUMP_IF_TRUE" => {
                    let jump_to: usize = operand.as_ref().unwrap().extract(py)?;
                    let val = self.stack.pop().unwrap();
                    let is_true: bool = val.extract(py)?;
                    if is_true {
                        self.ip = jump_to;
                    }
                }
                "JUMP_BACKWARD" => {
                    let jump_to: usize = operand.as_ref().unwrap().extract(py)?;
                    self.ip = jump_to;
                }
                "JUMP_FORWARD" => {
                    let jump_to: usize = operand.as_ref().unwrap().extract(py)?;
                    self.ip = jump_to;
                }
                "GET_ITER" => {
                    let obj = self.stack.pop().unwrap();
                    let iter = obj.call_method0(py, "__iter__")?;
                    self.stack.push(iter);
                }
                "FOR_ITER" => {
                    let jump_to: usize = operand.as_ref().unwrap().extract(py)?;
                    let iter = self.stack.last().unwrap().clone_ref(py);
                    match iter.call_method0(py, "__next__") {
                        Ok(val) => { self.stack.push(val); }
                        Err(_) => {
                            self.stack.pop();
                            self.ip = jump_to;
                        }
                    }
                }
                "MAKE_FUNCTION" => {
                    let func_data = self.stack.pop().unwrap();
                    self.stack.push(func_data);
                }
                "CALL_FUNCTION" => {
                    let arg_count: usize = operand.as_ref().unwrap().extract(py)?;
                    let mut args = Vec::new();
                    for _ in 0..arg_count {
                        args.push(self.stack.pop().unwrap());
                    }
                    args.reverse();
                    let func_data = self.stack.pop().unwrap();
                    let func_tuple = func_data.downcast_bound::<PyTuple>(py)?;
                    let name: String = func_tuple.get_item(0)?.extract()?;
                    let params: Vec<String> = func_tuple.get_item(1)?.extract()?;
                    let body_instrs: Vec<(String, Option<PyObject>)> = func_tuple.get_item(2)?.extract()?;
                    let body_consts: Vec<PyObject> = func_tuple.get_item(3)?.extract()?;
                    
                    let old_vars: HashMap<String, PyObject> = self.variables.iter().map(|(k, v)| (k.clone(), v.clone_ref(py))).collect();
                    let old_ip = self.ip;
                    let old_stack: Vec<PyObject> = self.stack.iter().map(|v| v.clone_ref(py)).collect();
                    
                    for (i, param) in params.iter().enumerate() {
                        if i < args.len() {
                            self.variables.insert(param.clone(), args[i].clone_ref(py));
                        }
                    }
                    
                    self.stack = Vec::new();
                    match self.run(py, body_instrs, body_consts) {
                        Ok(()) => {}
                        Err(e) => {
                            self.variables = old_vars;
                            self.ip = old_ip;
                            self.stack = old_stack;
                            return Err(e);
                        }
                    }
                    
                    let result = self.stack.last().map(|v| v.clone_ref(py));
                    self.stack = old_stack;
                    if let Some(val) = result {
                        self.stack.push(val);
                    } else {
                        self.stack.push(py.None());
                    }
                    self.variables = old_vars;
                    self.ip = old_ip;
                }
                "RETURN_VALUE" => {
                    break;
                }
                "PRINT" => {
                    let val = self.stack.pop().unwrap();
                    println!("{}", val.to_string());
                }
                "POP_TOP" => {
                    self.stack.pop();
                }
                _ => {
                    return Err(pyo3::exceptions::PyNotImplementedError::new_err(format!("Unknown opcode: {}", opcode)));
                }
            }
        }
        Ok(())
    }
}

#[pymodule]
fn pyliuno_vm(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<VM>()?;
    Ok(())
}