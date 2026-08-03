mod value;
mod vm2;
mod lexer2;
mod parser2;
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
    let tokens = lexer2::tokenize(&source);
    
    let mut parser = parser2::Parser::new(tokens);
    match parser.parse() {
        Ok((instructions, constants)) => {
            let mut vm = Vm::new();
            match vm.run(&instructions, &constants) {
                Ok(()) => {},
                Err(e) => eprintln!("Runtime error: {}", e),
            }
        }
        Err(e) => eprintln!("Parse error: {}", e),
    }
}