use crate::lexer2::{Token, TokenType};
use crate::value::Value;

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
    loop_end_stack: Vec<usize>,
    loop_start_stack: Vec<usize>,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Parser { tokens, pos: 0, loop_end_stack: Vec::new(), loop_start_stack: Vec::new() }
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
            Err(format!("Expected {:?} at line {}, got {:?}", tt, self.current().line, self.current().ttype))
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
        // print(...)
        if self.is_keyword("print") {
            self.advance();
            self.expect(TokenType::LParen)?;
            if self.current().ttype != TokenType::RParen {
                self.parse_expr(instrs, consts)?;
                while self.current().ttype == TokenType::Comma {
                    self.advance();
                    self.parse_expr(instrs, consts)?;
                }
            }
            self.expect(TokenType::RParen)?;
            instrs.push(("PRINT".into(), None));
            return Ok(());
        }

        if self.is_keyword("break") {
            self.advance();
            instrs.push(("BREAK_LOOP".into(), None));
            return Ok(());
        }
        if self.is_keyword("continue") {
            self.advance();
            let target = self.loop_start_stack.last().cloned().unwrap_or(0);
            instrs.push(("JUMP_BACKWARD".into(), Some(Value::Int(target as i64))));
            return Ok(());
        }
        if self.is_keyword("global") {
            self.advance();
            let name = self.expect(TokenType::Name)?.value.clone();
            instrs.push(("STORE_GLOBAL".into(), Some(Value::String(name))));
            return Ok(());
        }


        // if
        if self.is_keyword("if") {
            self.advance();
            self.parse_expr(instrs, consts)?;
            self.expect(TokenType::Colon)?;
            
            let jump_idx = instrs.len();
            instrs.push(("JUMP_IF_FALSE".into(), Some(Value::Int(0))));
            
            self.parse_block(instrs, consts)?;
            
            let has_else = self.is_keyword("else") || self.is_keyword("elif");
            let mut end_jump_idx = 0;
            if has_else {
                end_jump_idx = instrs.len();
                instrs.push(("JUMP_FORWARD".into(), Some(Value::Int(0))));
            }
            
            let after_body = instrs.len();
            instrs[jump_idx] = ("JUMP_IF_FALSE".into(), Some(Value::Int(after_body as i64)));
            
            while self.is_keyword("elif") || self.is_keyword("else") {
                self.advance();
                if self.current().ttype != TokenType::Colon {
                    self.parse_expr(instrs, consts)?;
                }
                self.expect(TokenType::Colon)?;
                self.parse_block(instrs, consts)?;
            }
            
            if has_else {
                let end = instrs.len();
                instrs[end_jump_idx] = ("JUMP_FORWARD".into(), Some(Value::Int(end as i64)));
            }
            return Ok(());
        }

        // while
        if self.is_keyword("while") {
            self.advance();
            let loop_start = instrs.len();
            self.loop_start_stack.push(loop_start);
            self.parse_expr(instrs, consts)?;
            self.expect(TokenType::Colon)?;
            let jump_idx = instrs.len();
            instrs.push(("JUMP_IF_FALSE".into(), Some(Value::Int(0))));
            self.loop_end_stack.push(0); // 占位
            self.parse_block(instrs, consts)?;
            let after_body = instrs.len();
            instrs.push(("JUMP_BACKWARD".into(), Some(Value::Int(loop_start as i64))));
            let end = instrs.len();
            *self.loop_end_stack.last_mut().unwrap() = end;
            instrs[jump_idx] = ("JUMP_IF_FALSE".into(), Some(Value::Int(end as i64)));
            // 回填 break
            let end = instrs.len();
            for i in 0..instrs.len() {
                if instrs[i].0 == "BREAK_LOOP" && instrs[i].1.is_none() {
                    instrs[i] = ("JUMP_FORWARD".into(), Some(Value::Int(end as i64)));
                }
            }
            self.loop_end_stack.pop();
            return Ok(());
        }

        // for
        if self.is_keyword("for") {
            self.advance();
            let var = self.expect(TokenType::Name)?.value.clone();
            self.expect(TokenType::Keyword)?;
            self.parse_expr(instrs, consts)?;
            self.expect(TokenType::Colon)?;
            
            instrs.push(("GET_ITER".into(), None));
            
            let loop_start = instrs.len();
            let for_jump_idx = instrs.len();
            instrs.push(("FOR_ITER".into(), Some(Value::Int(0))));
            
            instrs.push(("STORE_NAME".into(), Some(Value::String(var))));
            
            self.parse_block(instrs, consts)?;
            
            instrs.push(("JUMP_BACKWARD".into(), Some(Value::Int(loop_start as i64))));
            
            let after_body = instrs.len();
            instrs[for_jump_idx] = ("FOR_ITER".into(), Some(Value::Int(after_body as i64)));
            return Ok(());
        }

        // def
        if self.is_keyword("def") {
            self.advance();
            let name = self.expect(TokenType::Name)?.value.clone();
            self.expect(TokenType::LParen)?;
            let mut params = Vec::new();
            let mut defaults = Vec::new();
            if self.current().ttype == TokenType::Name {
                loop {
                    let pname = self.advance().value.clone();
                    let mut has_default = false;
                    if self.current().ttype == TokenType::Op && self.current().value == "=" {
                        self.advance();
                        has_default = true;
                        self.parse_expr(instrs, consts)?;
                    }
                    params.push(pname);
                    defaults.push(has_default);
                    if self.current().ttype == TokenType::Comma { self.advance(); } else { break; }
                }
            }
            self.expect(TokenType::RParen)?;
            self.expect(TokenType::Colon)?;
            let mut func_instrs = Vec::new();
            let mut func_consts = Vec::new();
            self.parse_block(&mut func_instrs, &mut func_consts)?;
            let func_value = Value::Function(crate::value::Function {
                name: name.clone(),
                params,
                body: func_instrs,
                constants: func_consts,
                defaults: defaults,
            });
            let idx = consts.len();
            consts.push(func_value);
            instrs.push(("LOAD_CONST".into(), Some(Value::Int(idx as i64))));
            instrs.push(("STORE_NAME".into(), Some(Value::String(name))));
            return Ok(());
        }

        // return
        if self.is_keyword("return") {
            self.advance();
            if self.current().ttype != TokenType::Newline && self.current().ttype != TokenType::Dedent {
                self.parse_expr(instrs, consts)?;
                let mut count = 1;
                while self.current().ttype == TokenType::Comma {
                    self.advance();
                    self.parse_expr(instrs, consts)?;
                    count += 1;
                }
                if count > 1 {
                    instrs.push(("BUILD_LIST".into(), Some(Value::Int(count))));
                }
            } else {
                let idx = consts.len();
                consts.push(Value::None);
                instrs.push(("LOAD_CONST".into(), Some(Value::Int(idx as i64))));
            }
            instrs.push(("RETURN_VALUE".into(), None));
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
            } else {
                self.pos -= 1;
                self.parse_expr(instrs, consts)?;
                instrs.push(("POP_TOP".into(), None));
                return Ok(());
            }
        }

        self.parse_expr(instrs, consts)?;
        instrs.push(("POP_TOP".into(), None));
        Ok(())
    }

    fn is_keyword(&self, kw: &str) -> bool {
        self.current().ttype == TokenType::Keyword && self.current().value == kw
    }

    fn parse_block(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.skip_newlines();
        self.expect(TokenType::Indent)?;
        while self.current().ttype != TokenType::Dedent && self.current().ttype != TokenType::Eof {
            self.skip_newlines();
            if self.current().ttype == TokenType::Dedent || self.current().ttype == TokenType::Eof { break; }
            self.parse_stmt(instrs, consts)?;
            self.skip_newlines();
        }
        if self.current().ttype == TokenType::Dedent {
            self.advance();
        }
        Ok(())
    }

    fn parse_expr(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_or(instrs, consts)
    }
    fn parse_or(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_xor(instrs, consts)?;
        while self.is_keyword("or") || self.is_keyword("nor") {
            let op = if self.current().value == "or" { "BINARY_OR" } else { "BINARY_NOR" };
            self.advance();
            self.parse_xor(instrs, consts)?;
            instrs.push((op.into(), None));
        }
        Ok(())
    }

    fn parse_xor(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_and(instrs, consts)?;
        while self.is_keyword("xor") {
            self.advance();
            self.parse_and(instrs, consts)?;
            instrs.push(("BINARY_XOR".into(), None));
        }
        Ok(())
    }

    fn parse_and(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_not(instrs, consts)?;
        while self.is_keyword("and") || self.is_keyword("nand") {
            let op = if self.current().value == "and" { "BINARY_AND" } else { "BINARY_NAND" };
            self.advance();
            self.parse_not(instrs, consts)?;
            instrs.push((op.into(), None));
        }
        Ok(())
    }

    fn parse_not(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        if self.is_keyword("not") {
            self.advance();
            self.parse_not(instrs, consts)?;
            instrs.push(("UNARY_NOT".into(), None));
        } else {
            self.parse_comparison(instrs, consts)?;
        }
        Ok(())
    }

    fn parse_sum(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
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

    fn parse_comparison(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_sum(instrs, consts)?;
        while (self.current().ttype == TokenType::Op && 
            ["==", "!=", "<", ">", "<=", ">="].contains(&self.current().value.as_str()))
            || (self.current().ttype == TokenType::Keyword && self.current().value == "in")
            || (self.current().ttype == TokenType::Keyword && self.current().value == "not" 
                && self.pos + 1 < self.tokens.len() && self.tokens[self.pos + 1].value == "in") {
            let op = self.current().value.clone();
            self.advance();
            if op == "not" {
                self.advance(); // 消费 "in"
                self.parse_sum(instrs, consts)?;
                instrs.push(("BINARY_NOT_IN".into(), None));
                continue;
            }
            self.parse_sum(instrs, consts)?;
            let instr = match op.as_str() {
                "==" => "COMPARE_EQ", "!=" => "COMPARE_NE",
                "<" => "COMPARE_LT", ">" => "COMPARE_GT",
                "<=" => "COMPARE_LE", ">=" => "COMPARE_GE",
                "in" => "BINARY_IN",
                _ => "COMPARE_EQ",
            };
            instrs.push((instr.into(), None));
        }
        Ok(())
    }

    fn parse_term(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        self.parse_factor(instrs, consts)?;
        while self.current().ttype == TokenType::Op && (self.current().value == "*" || self.current().value == "/" || self.current().value == "%") {
            let op = self.current().value.clone();
            self.advance();
            self.parse_factor(instrs, consts)?;
            let instr = match op.as_str() { "*" => "BINARY_MUL", "/" => "BINARY_DIV", "%" => "BINARY_MOD", _ => "BINARY_MUL" };
            instrs.push((instr.into(), None));
        }
        Ok(())
    }

    fn parse_factor(&mut self, instrs: &mut Vec<(String, Option<Value>)>, consts: &mut Vec<Value>) -> Result<(), String> {
        if self.current().ttype == TokenType::Op && (self.current().value == "-" || self.current().value == "+") {
            let op = self.current().value.clone();
            self.advance();
            self.parse_factor(instrs, consts)?;
            if op == "-" {
                let idx = consts.len();
                consts.push(Value::Int(0));
                instrs.push(("LOAD_CONST".into(), Some(Value::Int(idx as i64))));
                instrs.push(("BINARY_SUB".into(), None));
            }
            return Ok(());
        }

        if self.current().ttype == TokenType::Number {
            let n: i64 = self.current().value.parse().map_err(|_| "Invalid number".to_string())?;
            self.advance();
            let idx = consts.len();
            consts.push(Value::Int(n));
            instrs.push(("LOAD_CONST".into(), Some(Value::Int(idx as i64))));
            return Ok(());
        }

        if self.current().ttype == TokenType::String {
            let s = self.current().value.clone();
            self.advance();
            let idx = consts.len();
            consts.push(Value::String(s));
            instrs.push(("LOAD_CONST".into(), Some(Value::Int(idx as i64))));
            return Ok(());
        }

        if self.current().ttype == TokenType::Name {
            let name = self.current().value.clone();
            self.advance();
            instrs.push(("LOAD_NAME".into(), Some(Value::String(name.clone()))));
            // 下标访问
            while self.current().ttype == TokenType::LBracket {
                self.advance();
                self.parse_expr(instrs, consts)?;
                self.expect(TokenType::RBracket)?;
                instrs.push(("BINARY_SUBSCR".into(), None));
            }
            // 方法调用
            while self.current().ttype == TokenType::Dot {
                self.advance();
                let method = self.expect(TokenType::Name)?.value.clone();
                self.expect(TokenType::LParen)?;
                instrs.push(("LOAD_CONST".into(), Some(Value::String(method))));
                let mut arg_count = 0;
                if self.current().ttype != TokenType::RParen {
                    self.parse_expr(instrs, consts)?;
                    arg_count += 1;
                    while self.current().ttype == TokenType::Comma {
                        self.advance();
                        self.parse_expr(instrs, consts)?;
                        arg_count += 1;
                    }
                }
                self.expect(TokenType::RParen)?;
                instrs.push(("METHOD_CALL".into(), Some(Value::Int(arg_count))));
                instrs.push(("STORE_NAME".into(), Some(Value::String(name.clone()))));
            }
            if self.current().ttype == TokenType::LParen {
                self.advance();
                let mut arg_count = 0;
                if self.current().ttype != TokenType::RParen {
                    self.parse_expr(instrs, consts)?;
                    arg_count += 1;
                    while self.current().ttype == TokenType::Comma {
                        self.advance();
                        self.parse_expr(instrs, consts)?;
                        arg_count += 1;
                    }
                }
                self.expect(TokenType::RParen)?;
                instrs.push(("CALL_FUNCTION".into(), Some(Value::Int(arg_count))));
            }
            return Ok(());
        }
        // 字典 {key: value}
        if self.current().ttype == TokenType::LBrace {
            self.advance();
            let mut count = 0;
            if self.current().ttype != TokenType::RBrace {
                self.parse_expr(instrs, consts)?;
                self.expect(TokenType::Colon)?;
                self.parse_expr(instrs, consts)?;
                count += 1;
                while self.current().ttype == TokenType::Comma {
                    self.advance();
                    self.parse_expr(instrs, consts)?;
                    self.expect(TokenType::Colon)?;
                    self.parse_expr(instrs, consts)?;
                    count += 1;
                }
            }
            self.expect(TokenType::RBrace)?;
            instrs.push(("BUILD_DICT".into(), Some(Value::Int(count))));
            return Ok(());
        }

        // 列表 [1, 2, 3]
        if self.current().ttype == TokenType::LBracket {
            self.advance();
            if self.current().ttype == TokenType::RBracket {
                self.expect(TokenType::RBracket)?;
                instrs.push(("BUILD_LIST".into(), Some(Value::Int(0))));
                return Ok(());
            }
            self.parse_expr(instrs, consts)?;
            // 列表推导式 [expr for x in iter]
            if self.is_keyword("for") {
                self.advance();
                let var = self.expect(TokenType::Name)?.value.clone();
                self.expect(TokenType::Keyword)?; // in
                self.parse_expr(instrs, consts)?;
                self.expect(TokenType::RBracket)?;
                instrs.push(("BUILD_LIST_COMP".into(), Some(Value::String(var))));
                return Ok(());
            }
            let mut count = 1;
            while self.current().ttype == TokenType::Comma {
                self.advance();
                self.parse_expr(instrs, consts)?;
                count += 1;
            }
            self.expect(TokenType::RBracket)?;
            instrs.push(("BUILD_LIST".into(), Some(Value::Int(count))));
            return Ok(());
        }
        Err(format!("Unexpected token at line {}: {:?}", self.current().line, self.current()))
    }
}