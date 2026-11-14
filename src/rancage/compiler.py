"""RANCAGE 0.1 compiler: typed AST -> portable RANCAGE IR bytecode."""
from __future__ import annotations
from .ast import *

class Compiler:
    def __init__(self, program: Program):
        self.program = program

    def compile(self) -> dict:
        functions = {}
        for fn in self.program.functions:
            self.code = []
            for stmt in fn.body: self._stmt(stmt)
            # A final void return is harmless for void functions and unreachable after a required return.
            self.emit("PUSH", None)
            self.emit("RETURN")
            functions[fn.name] = {
                "params": [p.name for p in fn.params],
                "return_type": fn.return_type,
                "code": self.code,
            }
        return {
            "format": "RANCAGE-IR",
            "version": "0.1",
            "module": self.program.module,
            "entry": "main",
            "functions": functions,
        }

    def emit(self, op: str, *args) -> int:
        self.code.append([op, *args])
        return len(self.code) - 1

    def patch(self, index: int, target: int) -> None:
        self.code[index][1] = target

    def _stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, Let):
            self._expr(stmt.value); self.emit("STORE", stmt.name)
        elif isinstance(stmt, Assign):
            self._expr(stmt.value); self.emit("STORE", stmt.name)
        elif isinstance(stmt, Return):
            if stmt.value is None: self.emit("PUSH", None)
            else: self._expr(stmt.value)
            self.emit("RETURN")
        elif isinstance(stmt, ExprStmt):
            self._expr(stmt.value); self.emit("POP")
        elif isinstance(stmt, If):
            self._expr(stmt.condition)
            false_jump = self.emit("JUMP_IF_FALSE", -1)
            for child in stmt.then_body: self._stmt(child)
            if stmt.else_body is not None:
                end_jump = self.emit("JUMP", -1)
                self.patch(false_jump, len(self.code))
                for child in stmt.else_body: self._stmt(child)
                self.patch(end_jump, len(self.code))
            else:
                self.patch(false_jump, len(self.code))
        elif isinstance(stmt, While):
            start = len(self.code)
            self._expr(stmt.condition)
            end_jump = self.emit("JUMP_IF_FALSE", -1)
            for child in stmt.body: self._stmt(child)
            self.emit("JUMP", start)
            self.patch(end_jump, len(self.code))

    def _expr(self, expr: Expr) -> None:
        if isinstance(expr, Literal): self.emit("PUSH", expr.value)
        elif isinstance(expr, Name): self.emit("LOAD", expr.value)
        elif isinstance(expr, Unary):
            self._expr(expr.operand)
            self.emit("NOT" if expr.op == "!" else "NEG")
        elif isinstance(expr, Binary):
            self._expr(expr.left); self._expr(expr.right)
            mapping = {
                "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD",
                "==": "EQ", "!=": "NE", "<": "LT", "<=": "LE", ">": "GT", ">=": "GE",
                "&&": "AND", "||": "OR",
            }
            self.emit(mapping[expr.op])
        elif isinstance(expr, Call):
            for arg in expr.args: self._expr(arg)
            self.emit("CALL", expr.name, len(expr.args))
        else:
            raise ValueError(f"Ekspresi compiler tidak dikenal: {type(expr).__name__}")


def compile_program(program: Program) -> dict:
    return Compiler(program).compile()
