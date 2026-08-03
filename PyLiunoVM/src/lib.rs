use pyo3::prelude::*;
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