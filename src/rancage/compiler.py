"""RANCAGE 0.2 compiler: typed AST -> portable RANCAGE-IR 0.2 bytecode."""
from __future__ import annotations
from .ast import *


class RancageCompilerError(ValueError):
    def __init__(self, message: str, span: Span | None = None):
        if span:
            super().__init__(f"{message} (baris {span.line}, kolom {span.column})")
        else:
            super().__init__(message)
        self.span = span


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
        records = {}
        for rec in self.program.records:
            records[rec.name] = {
                "fields": [{"name": f.name, "type": f.type_name} for f in rec.fields]
            }
        return {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "module": self.program.module,
            "entry": "main",
            "records": records,
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
        elif isinstance(stmt, FieldAssign):
            self._expr(stmt.target)
            self._expr(stmt.value)
            self.emit("SET_FIELD", stmt.field)
        elif isinstance(stmt, IndexAssign):
            target_type = getattr(stmt.target, "inferred_type", None)
            if target_type is None:
                raise RancageCompilerError("Indexing assignment requires inferred type metadata from TypeChecker", stmt.span)
            self._expr(stmt.target)
            self._expr(stmt.index)
            self._expr(stmt.value)
            if target_type.startswith("list[") and target_type.endswith("]"):
                self.emit("LIST_SET")
            elif target_type.startswith("map[string, ") and target_type.endswith("]"):
                self.emit("MAP_SET")
            else:
                raise RancageCompilerError(f"Tipe target tidak mendukung penugasan indeks: {target_type}", stmt.span)
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
        else:
            raise ValueError(f"Pernyataan compiler tidak dikenal: {type(stmt).__name__}")

    def _expr(self, expr: Expr) -> None:
        if isinstance(expr, Literal): self.emit("PUSH", expr.value)
        elif isinstance(expr, NullLiteral): self.emit("PUSH", None)
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
        elif isinstance(expr, ListLiteral):
            for el in expr.elements:
                self._expr(el)
            self.emit("MAKE_LIST", len(expr.elements))
        elif isinstance(expr, MapLiteral):
            for k, v in expr.entries:
                self._expr(k)
                self._expr(v)
            self.emit("MAKE_MAP", len(expr.entries))
        elif isinstance(expr, RecordInit):
            for f in expr.fields:
                self._expr(f.value)
            self.emit("MAKE_RECORD", expr.name, [f.name for f in expr.fields])
        elif isinstance(expr, FieldAccess):
            self._expr(expr.target)
            self.emit("GET_FIELD", expr.field)
        elif isinstance(expr, IndexExpr):
            target_type = getattr(expr.target, "inferred_type", None)
            if target_type is None:
                raise RancageCompilerError("Indexing expression requires inferred type metadata from TypeChecker", expr.span)
            self._expr(expr.target)
            self._expr(expr.index)
            if target_type == "string":
                self.emit("STRING_GET")
            elif target_type.startswith("list[") and target_type.endswith("]"):
                self.emit("LIST_GET")
            elif target_type.startswith("map[string, ") and target_type.endswith("]"):
                self.emit("MAP_GET")
            else:
                raise RancageCompilerError(f"Tipe target tidak mendukung pengindeksan: {target_type}", expr.span)
        else:
            raise ValueError(f"Ekspresi compiler tidak dikenal: {type(expr).__name__}")


def compile_program(program: Program) -> dict:
    return Compiler(program).compile()
