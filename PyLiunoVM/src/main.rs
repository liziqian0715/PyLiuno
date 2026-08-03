mod value;
mod vm2;

use vm2::Vm;
use value::Value;

fn main() {
    // 测试程序：x = 10; print(x + 5)
    let instructions = vec![
        ("LOAD_CONST".to_string(), Some(Value::Int(0))),  // 0 -> constants[0]=10
        ("STORE_NAME".to_string(), Some(Value::String("x".to_string()))),
        ("LOAD_NAME".to_string(), Some(Value::String("x".to_string()))),
        ("LOAD_CONST".to_string(), Some(Value::Int(1))),  // 1 -> constants[1]=5
        ("BINARY_ADD".to_string(), None),
        ("PRINT".to_string(), None),
    ];
    
    let constants = vec![
        Value::Int(10),
        Value::Int(5),
    ];
    
    let mut vm = Vm::new();
    match vm.run(&instructions, &constants) {
        Ok(()) => {},
        Err(e) => eprintln!("Error: {}", e),
    }
}