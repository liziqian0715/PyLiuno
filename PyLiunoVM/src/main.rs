mod value;
mod vm2;

use vm2::Vm;
use value::Value;
use std::env;
use std::fs;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: pyliuno <file.pyl>");
        process::exit(1);
    }
    
    let path = &args[1];
    let source = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Error reading file: {}", e);
            process::exit(1);
        }
    };
    
    // 暂时只支持简单表达式
    // 完整版需要 Rust 写的 lexer + parser
    println!("Reading: {}", path);
    println!("Source: {}", source);
    
    // 用硬编码测试
    let instructions = vec![
        ("LOAD_CONST".to_string(), Some(Value::Int(0))),
        ("STORE_NAME".to_string(), Some(Value::String("x".to_string()))),
        ("LOAD_NAME".to_string(), Some(Value::String("x".to_string()))),
        ("LOAD_CONST".to_string(), Some(Value::Int(1))),
        ("BINARY_ADD".to_string(), None),
        ("PRINT".to_string(), None),
    ];
    
    let constants = vec![Value::Int(10), Value::Int(5)];
    
    let mut vm = Vm::new();
    match vm.run(&instructions, &constants) {
        Ok(()) => {},
        Err(e) => eprintln!("Error: {}", e),
    }
}