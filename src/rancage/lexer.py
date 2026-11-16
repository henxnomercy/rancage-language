"""Lexer for the RANCAGE language."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int

class RancageSyntaxError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.message, self.line, self.column = message, line, column

SINGLE = set("{}():,;+-*/%=<>![]?.")
DOUBLE = {"->", "==", "!=", "<=", ">=", "&&", "||"}
KEYWORDS = {"module", "fn", "let", "const", "return", "if", "else", "while", "record"}
RESERVED = KEYWORDS | {"null", "true", "false"}

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.i = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def _peek(self, offset: int = 0) -> str:
        p = self.i + offset
        return self.source[p] if p < len(self.source) else "\0"

    def _advance(self) -> str:
        ch = self._peek()
        if ch == "\0":
            return ch
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _add(self, kind: str, value: str, line: int, column: int) -> None:
        self.tokens.append(Token(kind, value, line, column))

    def tokenize(self) -> list[Token]:
        while self._peek() != "\0":
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
                continue
            if ch == "/" and self._peek(1) == "/":
                while self._peek() not in ("\n", "\0"):
                    self._advance()
                continue
            if ch == "/" and self._peek(1) == "*":
                start_line, start_col = self.line, self.column
                self._advance(); self._advance()
                while not (self._peek() == "*" and self._peek(1) == "/"):
                    if self._peek() == "\0":
                        raise RancageSyntaxError("Komentar blok tidak ditutup", start_line, start_col)
                    self._advance()
                self._advance(); self._advance()
                continue
            line, col = self.line, self.column
            if ch.isalpha() or ch == "_":
                chars = []
                while self._peek().isalnum() or self._peek() == "_":
                    chars.append(self._advance())
                self._add("IDENT", "".join(chars), line, col)
                continue
            if ch.isdigit():
                chars = []
                while self._peek().isdigit():
                    chars.append(self._advance())
                kind = "INT"
                if self._peek() == "." and self._peek(1).isdigit():
                    kind = "FLOAT"
                    chars.append(self._advance())
                    while self._peek().isdigit():
                        chars.append(self._advance())
                self._add(kind, "".join(chars), line, col)
                continue
            if ch == '"':
                self._advance()
                chars = []
                while self._peek() not in ('"', "\0"):
                    c = self._advance()
                    if c == "\n":
                        raise RancageSyntaxError("String tidak boleh melewati baris", line, col)
                    if c == "\\":
                        esc = self._advance()
                        mapping = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
                        if esc not in mapping:
                            raise RancageSyntaxError(f"Escape sequence tidak dikenal: \\{esc}", self.line, self.column)
                        chars.append(mapping[esc])
                    else:
                        chars.append(c)
                if self._peek() != '"':
                    raise RancageSyntaxError("String tidak ditutup", line, col)
                self._advance()
                self._add("STRING", "".join(chars), line, col)
                continue
            two = ch + self._peek(1)
            if two in DOUBLE:
                self._advance(); self._advance()
                self._add("SYMBOL", two, line, col)
                continue
            if ch in SINGLE:
                self._advance()
                self._add("SYMBOL", ch, line, col)
                continue
            raise RancageSyntaxError(f"Karakter tidak dikenal: {ch!r}", line, col)
        self._add("EOF", "", self.line, self.column)
        return self.tokens
