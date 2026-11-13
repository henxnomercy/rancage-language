"""Static type checker for the NOVA 0.1 core language."""
from __future__ import annotations
from dataclasses import dataclass
from .ast import *

VALID_TYPES = {"int", "float", "bool", "string", "void"}
NUMERIC = {"int", "float"}

class NovaTypeError(Exception):
    def __init__(self, message: str, span: Span):
        super().__init__(message)
        self.message, self.span = message, span

@dataclass(frozen=True)
class Signature:
    params: tuple[str, ...]
    returns: str

class TypeChecker:
    def __init__(self, program: Program):
        self.program = program
        self.signatures: dict[str, Signature] = {"print": Signature(("any",), "void")}

    def check(self) -> None:
        for fn in self.program.functions:
            if fn.name in self.signatures:
                raise NovaTypeError(f"Nama fungsi '{fn.name}' sudah digunakan", fn.span)
            if fn.return_type not in VALID_TYPES:
                raise NovaTypeError(f"Tipe return tidak dikenal: {fn.return_type}", fn.span)
            param_types = []
            names = set()
            for p in fn.params:
                if p.type_name not in VALID_TYPES - {"void"}:
                    raise NovaTypeError(f"Tipe parameter tidak valid: {p.type_name}", p.span)
                if p.name in names:
                    raise NovaTypeError(f"Parameter duplikat: {p.name}", p.span)
                names.add(p.name)
                param_types.append(p.type_name)
            self.signatures[fn.name] = Signature(tuple(param_types), fn.return_type)
        if "main" not in self.signatures:
            span = self.program.functions[0].span
            raise NovaTypeError("Program harus mendefinisikan fn main()", span)
        main = self.signatures["main"]
        if main.params or main.returns not in ("int", "void"):
            raise NovaTypeError("fn main harus tanpa parameter dan mengembalikan int atau void", self.program.functions[0].span)
        for fn in self.program.functions:
            env = {p.name: p.type_name for p in fn.params}
            consts: set[str] = set()
            declared_names = set(env)
            self._check_block(fn.body, env, consts, declared_names, fn.return_type)
            if fn.return_type != "void" and not self._always_returns(fn.body):
                raise NovaTypeError(f"Fungsi '{fn.name}' bertipe {fn.return_type} harus mengembalikan nilai pada semua jalur", fn.span)

    def _always_returns(self, body: list[Stmt]) -> bool:
        if not body:
            return False
        last = body[-1]
        if isinstance(last, Return):
            return True
        if isinstance(last, If) and last.else_body is not None:
            return self._always_returns(last.then_body) and self._always_returns(last.else_body)
        return False

    def _check_block(self, body: list[Stmt], env: dict[str, str], consts: set[str], declared_names: set[str], return_type: str) -> None:
        for stmt in body:
            if isinstance(stmt, Let):
                if stmt.name in declared_names:
                    raise NovaTypeError(f"Variabel '{stmt.name}' sudah dideklarasikan dalam fungsi ini", stmt.span)
                value_type = self._expr(stmt.value, env)
                declared = stmt.type_name or value_type
                if declared not in VALID_TYPES - {"void"}:
                    raise NovaTypeError(f"Tipe variabel tidak valid: {declared}", stmt.span)
                if declared != value_type:
                    raise NovaTypeError(f"Tidak bisa mengisi {declared} dengan nilai bertipe {value_type}", stmt.span)
                env[stmt.name] = declared
                declared_names.add(stmt.name)
                if stmt.is_const: consts.add(stmt.name)
            elif isinstance(stmt, Assign):
                if stmt.name not in env:
                    raise NovaTypeError(f"Variabel '{stmt.name}' belum dideklarasikan", stmt.span)
                if stmt.name in consts:
                    raise NovaTypeError(f"Konstanta '{stmt.name}' tidak bisa diubah", stmt.span)
                actual = self._expr(stmt.value, env)
                if actual != env[stmt.name]:
                    raise NovaTypeError(f"Tidak bisa mengisi {env[stmt.name]} dengan nilai bertipe {actual}", stmt.span)
            elif isinstance(stmt, Return):
                actual = "void" if stmt.value is None else self._expr(stmt.value, env)
                if actual != return_type:
                    raise NovaTypeError(f"Return fungsi harus {return_type}, bukan {actual}", stmt.span)
            elif isinstance(stmt, ExprStmt):
                self._expr(stmt.value, env)
            elif isinstance(stmt, If):
                cond = self._expr(stmt.condition, env)
                if cond != "bool": raise NovaTypeError("Kondisi if harus bertipe bool", stmt.span)
                self._check_block(stmt.then_body, dict(env), set(consts), declared_names, return_type)
                if stmt.else_body is not None:
                    self._check_block(stmt.else_body, dict(env), set(consts), declared_names, return_type)
            elif isinstance(stmt, While):
                cond = self._expr(stmt.condition, env)
                if cond != "bool": raise NovaTypeError("Kondisi while harus bertipe bool", stmt.span)
                self._check_block(stmt.body, dict(env), set(consts), declared_names, return_type)

    def _expr(self, expr: Expr, env: dict[str, str]) -> str:
        if isinstance(expr, Literal): return expr.type_name
        if isinstance(expr, Name):
            if expr.value not in env:
                raise NovaTypeError(f"Variabel '{expr.value}' belum dideklarasikan", expr.span)
            return env[expr.value]
        if isinstance(expr, Unary):
            operand = self._expr(expr.operand, env)
            if expr.op == "!" and operand == "bool": return "bool"
            if expr.op == "-" and operand in NUMERIC: return operand
            raise NovaTypeError(f"Operator unary '{expr.op}' tidak mendukung tipe {operand}", expr.span)
        if isinstance(expr, Binary):
            left, right = self._expr(expr.left, env), self._expr(expr.right, env)
            if expr.op in ("+", "-", "*", "/", "%"):
                if expr.op == "+" and left == right == "string": return "string"
                if left in NUMERIC and right in NUMERIC:
                    if expr.op == "/" or "float" in (left, right): return "float"
                    return "int"
                raise NovaTypeError(f"Operator '{expr.op}' tidak mendukung {left} dan {right}", expr.span)
            if expr.op in ("<", "<=", ">", ">="):
                if left in NUMERIC and right in NUMERIC: return "bool"
                raise NovaTypeError(f"Operator '{expr.op}' membutuhkan dua angka", expr.span)
            if expr.op in ("==", "!="):
                if left == right or (left in NUMERIC and right in NUMERIC): return "bool"
                raise NovaTypeError(f"Tidak bisa membandingkan {left} dengan {right}", expr.span)
            if expr.op in ("&&", "||"):
                if left == right == "bool": return "bool"
                raise NovaTypeError(f"Operator '{expr.op}' membutuhkan dua bool", expr.span)
        if isinstance(expr, Call):
            sig = self.signatures.get(expr.name)
            if sig is None:
                raise NovaTypeError(f"Fungsi '{expr.name}' tidak dikenal", expr.span)
            if len(expr.args) != len(sig.params):
                raise NovaTypeError(f"Fungsi '{expr.name}' membutuhkan {len(sig.params)} argumen, menerima {len(expr.args)}", expr.span)
            for i, (arg, expected) in enumerate(zip(expr.args, sig.params), start=1):
                actual = self._expr(arg, env)
                if expected != "any" and actual != expected:
                    raise NovaTypeError(f"Argumen {i} fungsi '{expr.name}' harus {expected}, bukan {actual}", expr.span)
            return sig.returns
        raise NovaTypeError("Ekspresi tidak didukung", getattr(expr, "span", Span(1, 1)))


def check_types(program: Program) -> None:
    TypeChecker(program).check()
