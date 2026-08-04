#[derive(Debug, Clone, PartialEq)]
pub enum TokenType {
    Number,
    String,
    Name,
    Keyword,
    Op,
    Colon,
    Comma,
    LParen,
    RParen,
    LBracket,
    RBracket,
    LBrace,
    RBrace,
    Dot,
    Newline,
    Indent,   // 只留一个
    Dedent,   // 只留一个
    Eof,
}

#[derive(Debug, Clone)]
pub struct Token {
    pub ttype: TokenType,
    pub value: String,
    pub line: usize,
    pub col: usize,
}

pub fn tokenize(source: &str) -> Vec<Token> {
    let mut tokens = Vec::new();
    let lines: Vec<&str> = source.lines().collect();
    let mut indent_stack: Vec<usize> = vec![0];
    let keywords: std::collections::HashSet<&str> = [
        "def", "if", "elif", "else", "while", "for", "return",
        "print", "break", "continue", "in", "and", "or", "not",
        "xor", "nand", "nor", "global", "try", "catch", "always",
        "True", "False", "None",
    ].iter().cloned().collect();

    for (line_num, line) in lines.iter().enumerate() {
        let line_num = line_num + 1;
        
        // 跳过空行和纯注释行
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        
        // 计算缩进
        let indent = line.len() - trimmed.len();
        
        if indent > *indent_stack.last().unwrap() {
            indent_stack.push(indent);
            tokens.push(Token { ttype: TokenType::Indent, value: "".into(), line: line_num, col: 1 });
        }
        while indent < *indent_stack.last().unwrap() {
            indent_stack.pop();
            tokens.push(Token { ttype: TokenType::Dedent, value: "".into(), line: line_num, col: 1 });
        }
        
        // 分词
        let mut col = indent + 1;
        let mut chars: Vec<char> = trimmed.chars().collect();
        let mut pos = 0;
        
        while pos < chars.len() {
            let ch = chars[pos];
            
            if ch == ' ' || ch == '\t' {
                pos += 1;
                col += 1;
                continue;
            }
            
            if ch == '#' {
                break; // 注释到行尾
            }
            
            // 数字
            if ch.is_ascii_digit() {
                let start = pos;
                while pos < chars.len() && chars[pos].is_ascii_digit() {
                    pos += 1;
                }
                let value: String = chars[start..pos].iter().collect();
                tokens.push(Token { ttype: TokenType::Number, value, line: line_num, col });
                col += pos - start;
                continue;
            }
            
            // 字符串
            if ch == '"' || ch == '\'' {
                let quote = ch;
                pos += 1;
                let start = pos;
                while pos < chars.len() && chars[pos] != quote {
                    pos += 1;
                }
                let value: String = chars[start..pos].iter().collect();
                if pos < chars.len() { pos += 1; }
                tokens.push(Token { ttype: TokenType::String, value, line: line_num, col });
                col += pos - start + 2;
                continue;
            }
            
            // 标识符或关键字
            if ch.is_ascii_alphabetic() || ch == '_' {
                let start = pos;
                while pos < chars.len() && (chars[pos].is_ascii_alphanumeric() || chars[pos] == '_') {
                    pos += 1;
                }
                let value: String = chars[start..pos].iter().collect();
                let ttype = if keywords.contains(value.as_str()) {
                    TokenType::Keyword
                } else {
                    TokenType::Name
                };
                tokens.push(Token { ttype, value, line: line_num, col });
                col += pos - start;
                continue;
            }
            
            // 运算符
            if "+-*/%<>=!".contains(ch) {
                let start = pos;
                pos += 1;
                if pos < chars.len() {
                    let two: String = vec![ch, chars[pos]].iter().collect();
                    if two == "==" || two == "!=" || two == "<=" || two == ">=" {
                        pos += 1;
                        tokens.push(Token { ttype: TokenType::Op, value: two, line: line_num, col });
                        col += 2;
                        continue;
                    }
                }
                tokens.push(Token { ttype: TokenType::Op, value: ch.to_string(), line: line_num, col });
                col += 1;
                continue;
            }
            
            // 分隔符
            let single = match ch {
                ':' => Some(TokenType::Colon),
                ',' => Some(TokenType::Comma),
                '(' => Some(TokenType::LParen),
                ')' => Some(TokenType::RParen),
                '[' => Some(TokenType::LBracket),
                ']' => Some(TokenType::RBracket),
                '{' => Some(TokenType::LBrace),
                '}' => Some(TokenType::RBrace),
                '.' => Some(TokenType::Dot),
                _ => None,
            };
            
            if let Some(tt) = single {
                tokens.push(Token { ttype: tt, value: ch.to_string(), line: line_num, col });
                pos += 1;
                col += 1;
            } else {
                pos += 1;
                col += 1;
            }
        }
        
        tokens.push(Token { ttype: TokenType::Newline, value: "\n".into(), line: line_num, col });
    }
    
    // 关闭所有缩进
    while indent_stack.len() > 1 {
        indent_stack.pop();
        tokens.push(Token { ttype: TokenType::Dedent, value: "".into(), line: 0, col: 1 });
    }
    
    tokens.push(Token { ttype: TokenType::Eof, value: String::new(), line: 0, col: 1 });
    tokens
}