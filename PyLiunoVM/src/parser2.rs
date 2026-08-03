use crate::lexer2::{Token, TokenType};
use crate::value::Value;

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Parser { tokens, pos: 0 }
    }

    fn current(&self) -> &Token {
        &self.tokens[self.pos]
    }

    fn advance(&mut self) -> &Token {
        let t = &self.tokens[self.pos];
        self.pos += 1;
        t
    }

    fn expect(&mut self, tt: TokenType) -> Result<&Token, String> {
        if self.current().ttype == tt {
            Ok(self.advance())
        } else {
            Err(format!("Expected {:?}, got {:?}", tt, self.current().ttype))
        }
    }

    fn skip_newlines(&mut self) {
        while self.current().ttype == TokenType::Newline {
            self.pos += 1;
        }
    }

    pub fn parse(&mut self) -> Result<(Vec<(String, Option<Value>)>, Vec<Value>), String> {
        let mut instructions = Vec::new();
        let mut constants = Vec::new();

        while self.current().ttype != TokenType::Eof {
            self.skip_newlines();
            if self.current().ttype == TokenType::Eof { break; }
            self.parse_stmt(&mut instructions, &mut constants)?;
        }

        Ok((instructions, constants))
    }

    fn parse_stmt(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        // print(expr)
        if self.current().ttype == TokenType::Keyword && self.current().value == "print" {
            self.advance();
            self.expect(TokenType::LParen)?;
            self.parse_expr(instrs, consts)?;
            self.expect(TokenType::RParen)?;
            instrs.push(("PRINT".into(), None));
            return Ok(());
        }

        // NAME = expr
        if self.current().ttype == TokenType::Name {
            let name = self.current().value.clone();
            self.advance();
            if self.current().ttype == TokenType::Op && self.current().value == "=" {
                self.advance();
                self.parse_expr(instrs, consts)?;
                instrs.push(("STORE_NAME".into(), Some(Value::String(name))));
                return Ok(());
            }
        }

        // 表达式语句
        self.parse_expr(instrs, consts)?;
        instrs.push(("POP_TOP".into(), None));
        Ok(())
    }

    fn parse_expr(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_term(instrs, consts)?;
        while self.current().ttype == TokenType::Op && (self.current().value == "+" || self.current().value == "-") {
            let op = self.current().value.clone();
            self.advance();
            self.parse_term(instrs, consts)?;
            let instr = if op == "+" { "BINARY_ADD" } else { "BINARY_SUB" };
            instrs.push((instr.into(), None));
        }
        Ok(())
    }

    fn parse_term(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_factor(instrs, consts)?;
        while self.current().ttype == TokenType::Op && (self.current().value == "*" || self.current().value == "/") {
            let op = self.current().value.clone();
            self.advance();
            self.parse_factor(instrs, consts)?;
            let instr = if op == "*" { "BINARY_MUL" } else { "BINARY_DIV" };
            instrs.push((instr.into(), None));
        }
        Ok(())
    }

    fn parse_factor(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        let t = self.advance();
        match t.ttype {
            TokenType::Number => {
                let n: i64 = t.value.parse().map_err(|_| "Invalid number".to_string())?;
                let idx = consts.len();
                consts.push(Value::Int(n));
                instrs.push(("LOAD_CONST".into(), Some(Value::Int(idx as i64))));
            }
            TokenType::Name => {
                instrs.push(("LOAD_NAME".into(), Some(Value::String(t.value.clone()))));
            }
            TokenType::LParen => {
                self.parse_expr(instrs, consts)?;
                self.expect(TokenType::RParen)?;
            }
            _ => return Err(format!("Unexpected token: {:?}", t)),
        }
        Ok(())
    }
}