"""Recursive-descent parser and Pratt expression parser for NOVA 0.1."""
from __future__ import annotations
from .ast import *
from .lexer import Lexer, Token, NovaSyntaxError

PRECEDENCE = {"||": 1, "&&": 2, "==": 3, "!=": 3, "<": 4, "<=": 4, ">": 4, ">=": 4,
              "+": 5, "-": 5, "*": 6, "/": 6, "%": 6}

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    def current(self) -> Token:
        return self.tokens[self.i]

    def check(self, value: str) -> bool:
        return self.current().value == value

    def advance(self) -> Token:
        tok = self.current()
        if tok.kind != "EOF": self.i += 1
        return tok

    def match(self, value: str) -> bool:
        if self.check(value):
            self.advance(); return True
        return False

    def expect(self, value: str, message: str | None = None) -> Token:
        if self.check(value): return self.advance()
        tok = self.current()
        raise NovaSyntaxError(message or f"Diharapkan {value!r}, ditemukan {tok.value!r}", tok.line, tok.column)

    def identifier(self, message: str = "Diharapkan nama identifier") -> Token:
        tok = self.current()
        if tok.kind != "IDENT": raise NovaSyntaxError(message, tok.line, tok.column)
        return self.advance()

    def parse(self) -> Program:
        module = "main"
        if self.match("module"):
            module = self.identifier("Diharapkan nama module").value
            self.expect(";")
        functions = []
        while self.current().kind != "EOF":
            functions.append(self.function())
        if not functions:
            tok = self.current()
            raise NovaSyntaxError("Program harus memiliki minimal satu fungsi", tok.line, tok.column)
        return Program(functions, module)

    def function(self) -> Function:
        start = self.expect("fn", "Program tingkat atas hanya boleh berisi deklarasi fn")
        name = self.identifier("Diharapkan nama fungsi")
        self.expect("(")
        params = []
        if not self.check(")"):
            while True:
                p = self.identifier("Diharapkan nama parameter")
                self.expect(":")
                t = self.identifier("Diharapkan tipe parameter")
                params.append(Param(p.value, t.value, Span(p.line, p.column)))
                if not self.match(","): break
        self.expect(")")
        self.expect("->", "Diharapkan '->' sebelum tipe return")
        ret = self.identifier("Diharapkan tipe return").value
        body = self.block()
        return Function(name.value, params, ret, body, Span(start.line, start.column))

    def block(self) -> list[Stmt]:
        self.expect("{")
        body = []
        while not self.check("}"):
            if self.current().kind == "EOF":
                tok = self.current(); raise NovaSyntaxError("Blok tidak ditutup dengan '}'", tok.line, tok.column)
            body.append(self.statement())
        self.expect("}")
        return body

    def statement(self) -> Stmt:
        tok = self.current()
        if self.match("let") or self.match("const"):
            is_const = self.tokens[self.i - 1].value == "const"
            name = self.identifier("Diharapkan nama variabel")
            type_name = None
            if self.match(":"):
                type_name = self.identifier("Diharapkan tipe variabel").value
            self.expect("=", "Deklarasi variabel harus memiliki nilai awal")
            value = self.expression()
            self.expect(";")
            return Let(name.value, type_name, value, is_const, Span(tok.line, tok.column))
        if self.match("return"):
            value = None if self.check(";") else self.expression()
            self.expect(";")
            return Return(value, Span(tok.line, tok.column))
        if self.match("if"):
            self.expect("(")
            condition = self.expression()
            self.expect(")")
            then_body = self.block()
            else_body = self.block() if self.match("else") else None
            return If(condition, then_body, else_body, Span(tok.line, tok.column))
        if self.match("while"):
            self.expect("(")
            condition = self.expression()
            self.expect(")")
            return While(condition, self.block(), Span(tok.line, tok.column))
        if tok.kind == "IDENT" and self.tokens[self.i + 1].value == "=":
            name = self.advance()
            self.advance()
            value = self.expression()
            self.expect(";")
            return Assign(name.value, value, Span(tok.line, tok.column))
        value = self.expression()
        self.expect(";")
        return ExprStmt(value, Span(tok.line, tok.column))

    def expression(self, min_prec: int = 1) -> Expr:
        tok = self.advance()
        if tok.value in ("!", "-"):
            left: Expr = Unary(tok.value, self.expression(7), Span(tok.line, tok.column))
        elif tok.value == "(":
            left = self.expression()
            self.expect(")")
        elif tok.kind == "INT":
            left = Literal(int(tok.value), "int", Span(tok.line, tok.column))
        elif tok.kind == "FLOAT":
            left = Literal(float(tok.value), "float", Span(tok.line, tok.column))
        elif tok.kind == "STRING":
            left = Literal(tok.value, "string", Span(tok.line, tok.column))
        elif tok.value in ("true", "false"):
            left = Literal(tok.value == "true", "bool", Span(tok.line, tok.column))
        elif tok.kind == "IDENT":
            if self.match("("):
                args = []
                if not self.check(")"):
                    while True:
                        args.append(self.expression())
                        if not self.match(","): break
                self.expect(")")
                left = Call(tok.value, args, Span(tok.line, tok.column))
            else:
                left = Name(tok.value, Span(tok.line, tok.column))
        else:
            raise NovaSyntaxError(f"Diharapkan ekspresi, ditemukan {tok.value!r}", tok.line, tok.column)
        while True:
            op = self.current().value
            prec = PRECEDENCE.get(op, 0)
            if prec < min_prec: break
            op_tok = self.advance()
            right = self.expression(prec + 1)
            left = Binary(left, op_tok.value, right, Span(op_tok.line, op_tok.column))
        return left


def parse_source(source: str) -> Program:
    return Parser(Lexer(source).tokenize()).parse()
