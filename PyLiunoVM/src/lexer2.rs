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
    Indent,
    Dedent,
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
    let mut chars: Vec<char> = source.chars().collect();
    let mut pos = 0;
    let mut line = 1;
    let mut col = 1;

    let keywords: std::collections::HashSet<&str> = [
        "def", "if", "elif", "else", "while", "for", "return",
        "print", "break", "continue", "in", "and", "or", "not",
        "xor", "nand", "nor", "global", "try", "catch", "always",
        "True", "False", "None",
    ].iter().cloned().collect();

    while pos < chars.len() {
        let ch = chars[pos];

        // 跳过空格
        if ch == ' ' || ch == '\t' {
            pos += 1;
            col += 1;
            continue;
        }

        // 换行
        if ch == '\n' {
            tokens.push(Token { ttype: TokenType::Newline, value: "\n".into(), line, col });
            pos += 1;
            line += 1;
            col = 1;
            continue;
        }

        // 注释
        if ch == '#' {
            while pos < chars.len() && chars[pos] != '\n' {
                pos += 1;
            }
            continue;
        }

        // 数字
        if ch.is_ascii_digit() {
            let start = pos;
            while pos < chars.len() && chars[pos].is_ascii_digit() {
                pos += 1;
            }
            let value: String = chars[start..pos].iter().collect();
            tokens.push(Token { ttype: TokenType::Number, value, line, col });
            col += pos - start;
            continue;
        }

        // 字符串
        if ch == '"' || ch == '\'' {
            let quote = ch;
            pos += 1;
            let start = pos;
            while pos < chars.len() && chars[pos] != quote {
                if chars[pos] == '\n' { break; }
                pos += 1;
            }
            let value: String = chars[start..pos].iter().collect();
            if pos < chars.len() { pos += 1; } // skip closing quote
            tokens.push(Token { ttype: TokenType::String, value, line, col });
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
            tokens.push(Token { ttype, value, line, col });
            col += pos - start;
            continue;
        }

        // 运算符
        if "+-*/%<>=!".contains(ch) {
            let start = pos;
            pos += 1;
            // 双字符运算符
            if pos < chars.len() {
                let two: String = vec![ch, chars[pos]].iter().collect();
                if two == "==" || two == "!=" || two == "<=" || two == ">=" {
                    pos += 1;
                    tokens.push(Token { ttype: TokenType::Op, value: two, line, col });
                    col += 2;
                    continue;
                }
            }
            tokens.push(Token { ttype: TokenType::Op, value: ch.to_string(), line, col });
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
            tokens.push(Token { ttype: tt, value: ch.to_string(), line, col });
            pos += 1;
            col += 1;
        } else {
            // 未知字符，跳过
            pos += 1;
            col += 1;
        }
    }

    tokens.push(Token { ttype: TokenType::Eof, value: String::new(), line, col });
    tokens
}