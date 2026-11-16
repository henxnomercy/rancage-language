"""Static type checker for the RANCAGE 0.1 and 0.2 Stage 0 language."""
from __future__ import annotations
from dataclasses import dataclass
from .ast import *

VALID_PRIMITIVES = {"int", "float", "bool", "string", "void"}
NUMERIC = {"int", "float"}
INTRINSICS = {"print", "len", "push", "pop", "ord", "chr", "slice", "map_has", "map_remove"}

class RancageTypeError(Exception):
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
        self.records: dict[str, RecordDecl] = {}

    def is_valid_type(self, t: str) -> bool:
        if t.endswith("?"):
            base = t[:-1]
            if base.endswith("?") or base == "void":
                return False
            return self.is_valid_type(base)
        if t in VALID_PRIMITIVES:
            return True
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1]
            return inner != "void" and self.is_valid_type(inner)
        if t.startswith("map[string, ") and t.endswith("]"):
            inner = t[12:-1]
            return inner != "void" and self.is_valid_type(inner)
        if t in self.records:
            return True
        return False

    def is_valid_value_type(self, t: str) -> bool:
        return t != "void" and self.is_valid_type(t)

    def is_assignable(self, target: str, source: str) -> bool:
        if target == source:
            return True
        if target.endswith("?"):
            target_base = target[:-1]
            if source == "null":
                return True
            if source.endswith("?"):
                return self.is_assignable(target_base, source[:-1])
            return self.is_assignable(target_base, source)
        return False

    def check(self) -> None:
        for rec in self.program.records:
            if rec.name in self.records:
                raise RancageTypeError(f"Record '{rec.name}' sudah dideklarasikan", rec.span)
            if rec.name in VALID_PRIMITIVES:
                raise RancageTypeError(f"Nama record '{rec.name}' bertabrakan dengan tipe primitif", rec.span)
            self.records[rec.name] = rec

        for rec in self.program.records:
            field_names: set[str] = set()
            for f in rec.fields:
                if f.name in field_names:
                    raise RancageTypeError(f"Field duplikat '{f.name}' pada record '{rec.name}'", f.span)
                field_names.add(f.name)
                if not self.is_valid_value_type(f.type_name):
                    raise RancageTypeError(f"Tipe field '{f.type_name}' pada record '{rec.name}' tidak valid", f.span)

        for fn in self.program.functions:
            if fn.name in self.signatures or fn.name in INTRINSICS:
                raise RancageTypeError(f"Nama fungsi '{fn.name}' sudah digunakan", fn.span)
            if not self.is_valid_type(fn.return_type):
                raise RancageTypeError(f"Tipe return tidak dikenal: {fn.return_type}", fn.span)
            param_types = []
            names = set()
            for p in fn.params:
                if not self.is_valid_value_type(p.type_name):
                    raise RancageTypeError(f"Tipe parameter tidak valid: {p.type_name}", p.span)
                if p.name in names:
                    raise RancageTypeError(f"Parameter duplikat: {p.name}", p.span)
                names.add(p.name)
                param_types.append(p.type_name)
            self.signatures[fn.name] = Signature(tuple(param_types), fn.return_type)

        if "main" not in self.signatures:
            span = self.program.functions[0].span if self.program.functions else Span(1, 1)
            raise RancageTypeError("Program harus mendefinisikan fn main()", span)
        main = self.signatures["main"]
        if main.params or main.returns not in ("int", "void"):
            raise RancageTypeError("fn main harus tanpa parameter dan mengembalikan int atau void", self.program.functions[0].span)

        for fn in self.program.functions:
            env = {p.name: p.type_name for p in fn.params}
            consts: set[str] = set()
            declared_names = set(env)
            self._check_block(fn.body, env, consts, declared_names, fn.return_type)
            if fn.return_type != "void" and not self._always_returns(fn.body):
                raise RancageTypeError(f"Fungsi '{fn.name}' bertipe {fn.return_type} harus mengembalikan nilai pada semua jalur", fn.span)

    def _always_returns(self, body: list[Stmt]) -> bool:
        if not body:
            return False
        last = body[-1]
        if isinstance(last, Return):
            return True
        if isinstance(last, If) and last.else_body is not None:
            return self._always_returns(last.then_body) and self._always_returns(last.else_body)
        return False

    def _get_root_name(self, expr: Expr) -> str | None:
        if isinstance(expr, Name):
            return expr.value
        if isinstance(expr, FieldAccess):
            return self._get_root_name(expr.target)
        if isinstance(expr, IndexExpr):
            return self._get_root_name(expr.target)
        return None

    def _check_block(self, body: list[Stmt], env: dict[str, str], consts: set[str], declared_names: set[str], return_type: str) -> None:
        for stmt in body:
            if isinstance(stmt, Let):
                if stmt.name in declared_names:
                    raise RancageTypeError(f"Variabel '{stmt.name}' sudah dideklarasikan dalam fungsi ini", stmt.span)
                expected = stmt.type_name
                value_type = self._expr(stmt.value, env, expected, consts)
                if stmt.type_name is None and value_type == "null":
                    raise RancageTypeError("Variabel dengan nilai null membutuhkan anotasi tipe eksplisit", stmt.span)
                declared = expected or value_type
                if not self.is_valid_value_type(declared):
                    raise RancageTypeError(f"Tipe variabel tidak valid: {declared}", stmt.span)
                if not self.is_assignable(declared, value_type):
                    raise RancageTypeError(f"Tidak bisa mengisi {declared} dengan nilai bertipe {value_type}", stmt.span)
                env[stmt.name] = declared
                declared_names.add(stmt.name)
                if stmt.is_const:
                    consts.add(stmt.name)
            elif isinstance(stmt, Assign):
                if stmt.name not in env:
                    raise RancageTypeError(f"Variabel '{stmt.name}' belum dideklarasikan", stmt.span)
                if stmt.name in consts:
                    raise RancageTypeError(f"Konstanta '{stmt.name}' tidak bisa diubah", stmt.span)
                target_type = env[stmt.name]
                actual = self._expr(stmt.value, env, target_type, consts)
                if not self.is_assignable(target_type, actual):
                    raise RancageTypeError(f"Tidak bisa mengisi {target_type} dengan nilai bertipe {actual}", stmt.span)
            elif isinstance(stmt, FieldAssign):
                root = self._get_root_name(stmt.target)
                if root is not None and root in consts:
                    raise RancageTypeError(f"Konstanta '{root}' tidak bisa diubah", stmt.span)
                target_type = self._expr(stmt.target, env, None, consts)
                rec_name = target_type[:-1] if target_type.endswith("?") else target_type
                if rec_name not in self.records:
                    raise RancageTypeError(f"Tipe '{target_type}' bukan record, tidak memiliki field '{stmt.field}'", stmt.span)
                rec_decl = self.records[rec_name]
                field_dict = {f.name: f.type_name for f in rec_decl.fields}
                if stmt.field not in field_dict:
                    raise RancageTypeError(f"Field '{stmt.field}' tidak ditemukan pada record '{rec_name}'", stmt.span)
                field_expected = field_dict[stmt.field]
                actual = self._expr(stmt.value, env, field_expected, consts)
                if not self.is_assignable(field_expected, actual):
                    raise RancageTypeError(f"Tidak bisa mengisi {field_expected} dengan nilai bertipe {actual}", stmt.span)
            elif isinstance(stmt, IndexAssign):
                root = self._get_root_name(stmt.target)
                if root is not None and root in consts:
                    raise RancageTypeError(f"Konstanta '{root}' tidak bisa diubah", stmt.span)
                target_type = self._expr(stmt.target, env, None, consts)
                if target_type == "string":
                    raise RancageTypeError("String bersifat immutable dan tidak bisa diubah melalui pengindeksan", stmt.span)
                if target_type.startswith("list[") and target_type.endswith("]"):
                    idx_type = self._expr(stmt.index, env, None, consts)
                    if idx_type != "int":
                        raise RancageTypeError(f"Index list harus bertipe int, bukan {idx_type}", stmt.span)
                    elem_type = target_type[5:-1]
                    actual = self._expr(stmt.value, env, elem_type, consts)
                    if not self.is_assignable(elem_type, actual):
                        raise RancageTypeError(f"Tidak bisa mengisi {elem_type} dengan nilai bertipe {actual}", stmt.span)
                elif target_type.startswith("map[string, ") and target_type.endswith("]"):
                    idx_type = self._expr(stmt.index, env, None, consts)
                    if idx_type != "string":
                        raise RancageTypeError(f"Key map harus bertipe string, bukan {idx_type}", stmt.span)
                    val_type = target_type[12:-1]
                    actual = self._expr(stmt.value, env, val_type, consts)
                    if not self.is_assignable(val_type, actual):
                        raise RancageTypeError(f"Tidak bisa mengisi {val_type} dengan nilai bertipe {actual}", stmt.span)
                else:
                    raise RancageTypeError(f"Tipe '{target_type}' tidak mendukung penugasan indeks", stmt.span)
            elif isinstance(stmt, Return):
                actual = "void" if stmt.value is None else self._expr(stmt.value, env, return_type, consts)
                if not self.is_assignable(return_type, actual):
                    raise RancageTypeError(f"Return fungsi harus {return_type}, bukan {actual}", stmt.span)
            elif isinstance(stmt, ExprStmt):
                self._expr(stmt.value, env, None, consts)
            elif isinstance(stmt, If):
                cond = self._expr(stmt.condition, env, None, consts)
                if cond != "bool":
                    raise RancageTypeError("Kondisi if harus bertipe bool", stmt.span)
                self._check_block(stmt.then_body, dict(env), set(consts), declared_names, return_type)
                if stmt.else_body is not None:
                    self._check_block(stmt.else_body, dict(env), set(consts), declared_names, return_type)
            elif isinstance(stmt, While):
                cond = self._expr(stmt.condition, env, None, consts)
                if cond != "bool":
                    raise RancageTypeError("Kondisi while harus bertipe bool", stmt.span)
                self._check_block(stmt.body, dict(env), set(consts), declared_names, return_type)

    def _expr(self, expr: Expr, env: dict[str, str], expected: str | None = None, consts: set[str] | None = None) -> str:
        t = self._eval_expr(expr, env, expected, consts)
        expr.inferred_type = t
        return t

    def _eval_expr(self, expr: Expr, env: dict[str, str], expected: str | None = None, consts: set[str] | None = None) -> str:
        if isinstance(expr, Literal):
            return expr.type_name
        if isinstance(expr, NullLiteral):
            if expected is not None and expected.endswith("?"):
                return expected
            return "null"
        if isinstance(expr, ListLiteral):
            if not expr.elements:
                if expected is not None and expected.startswith("list[") and expected.endswith("]"):
                    return expected
                if expected is not None and expected.endswith("?") and expected[:-1].startswith("list["):
                    return expected[:-1]
                raise RancageTypeError("Inisialisasi list kosong membutuhkan anotasi tipe eksplisit", expr.span)
            elem_expected = None
            if expected is not None and expected.startswith("list[") and expected.endswith("]"):
                elem_expected = expected[5:-1]
            elif expected is not None and expected.endswith("?") and expected[:-1].startswith("list["):
                elem_expected = expected[:-1][5:-1]
            first_type = self._expr(expr.elements[0], env, elem_expected, consts)
            for elem in expr.elements[1:]:
                elem_type = self._expr(elem, env, first_type, consts)
                if elem_type != first_type and not self.is_assignable(first_type, elem_type):
                    raise RancageTypeError(f"Elemen list tidak konsisten: diharapkan {first_type}, ditemukan {elem_type}", elem.span)
            return f"list[{first_type}]"
        if isinstance(expr, MapLiteral):
            if not expr.entries:
                if expected is not None and expected.startswith("map[string, ") and expected.endswith("]"):
                    return expected
                if expected is not None and expected.endswith("?") and expected[:-1].startswith("map[string, "):
                    return expected[:-1]
                raise RancageTypeError("Inisialisasi map kosong membutuhkan anotasi tipe eksplisit", expr.span)
            val_expected = None
            if expected is not None and expected.startswith("map[string, ") and expected.endswith("]"):
                val_expected = expected[12:-1]
            elif expected is not None and expected.endswith("?") and expected[:-1].startswith("map[string, "):
                val_expected = expected[:-1][12:-1]
            first_val_type = None
            for key_expr, val_expr in expr.entries:
                key_type = self._expr(key_expr, env, "string", consts)
                if key_type != "string":
                    raise RancageTypeError(f"Key map harus bertipe string, bukan {key_type}", key_expr.span)
                v_type = self._expr(val_expr, env, val_expected or first_val_type, consts)
                if first_val_type is None:
                    first_val_type = v_type
                elif v_type != first_val_type and not self.is_assignable(first_val_type, v_type):
                    raise RancageTypeError(f"Nilai map tidak konsisten: diharapkan {first_val_type}, ditemukan {v_type}", val_expr.span)
            return f"map[string, {first_val_type}]"
        if isinstance(expr, RecordInit):
            if expr.name not in self.records:
                raise RancageTypeError(f"Record '{expr.name}' tidak dikenal", expr.span)
            rec_decl = self.records[expr.name]
            expected_fields = {f.name: f.type_name for f in rec_decl.fields}
            seen_fields: set[str] = set()
            for f in expr.fields:
                if f.name in seen_fields:
                    raise RancageTypeError(f"Field duplikat '{f.name}' pada inisialisasi record '{expr.name}'", f.span)
                seen_fields.add(f.name)
                if f.name not in expected_fields:
                    raise RancageTypeError(f"Record '{expr.name}' tidak memiliki field '{f.name}'", f.span)
                f_expected = expected_fields[f.name]
                f_actual = self._expr(f.value, env, f_expected, consts)
                if not self.is_assignable(f_expected, f_actual):
                    raise RancageTypeError(f"Tidak bisa mengisi field '{f.name}' bertipe {f_expected} dengan nilai {f_actual}", f.span)
            missing = set(expected_fields) - seen_fields
            if missing:
                raise RancageTypeError(f"Inisialisasi record '{expr.name}' kekurangan field: {', '.join(sorted(missing))}", expr.span)
            return expr.name
        if isinstance(expr, FieldAccess):
            target_type = self._expr(expr.target, env, None, consts)
            rec_name = target_type[:-1] if target_type.endswith("?") else target_type
            if rec_name not in self.records:
                raise RancageTypeError(f"Tipe '{target_type}' bukan record, tidak memiliki field '{expr.field}'", expr.span)
            rec_decl = self.records[rec_name]
            field_dict = {f.name: f.type_name for f in rec_decl.fields}
            if expr.field not in field_dict:
                raise RancageTypeError(f"Field '{expr.field}' tidak ditemukan pada record '{rec_name}'", expr.span)
            return field_dict[expr.field]
        if isinstance(expr, IndexExpr):
            target_type = self._expr(expr.target, env, None, consts)
            idx_type = self._expr(expr.index, env, None, consts)
            if target_type == "string":
                if idx_type != "int":
                    raise RancageTypeError(f"Index string harus bertipe int, bukan {idx_type}", expr.span)
                return "string"
            if target_type.startswith("list[") and target_type.endswith("]"):
                if idx_type != "int":
                    raise RancageTypeError(f"Index list harus bertipe int, bukan {idx_type}", expr.span)
                return target_type[5:-1]
            if target_type.startswith("map[string, ") and target_type.endswith("]"):
                if idx_type != "string":
                    raise RancageTypeError(f"Key map harus bertipe string, bukan {idx_type}", expr.span)
                return target_type[12:-1]
            raise RancageTypeError(f"Tipe '{target_type}' tidak mendukung pengindeksan", expr.span)
        if isinstance(expr, Name):
            if expr.value not in env:
                raise RancageTypeError(f"Variabel '{expr.value}' belum dideklarasikan", expr.span)
            return env[expr.value]
        if isinstance(expr, Unary):
            operand = self._expr(expr.operand, env, None, consts)
            if expr.op == "!" and operand == "bool": return "bool"
            if expr.op == "-" and operand in NUMERIC: return operand
            raise RancageTypeError(f"Operator unary '{expr.op}' tidak mendukung tipe {operand}", expr.span)
        if isinstance(expr, Binary):
            left = self._expr(expr.left, env, None, consts)
            right = self._expr(expr.right, env, None, consts)
            if expr.op in ("+", "-", "*", "/", "%"):
                if expr.op == "+" and left == right == "string": return "string"
                if left in NUMERIC and right in NUMERIC:
                    if expr.op == "/" or "float" in (left, right): return "float"
                    return "int"
                raise RancageTypeError(f"Operator '{expr.op}' tidak mendukung {left} dan {right}", expr.span)
            if expr.op in ("<", "<=", ">", ">="):
                if left in NUMERIC and right in NUMERIC: return "bool"
                raise RancageTypeError(f"Operator '{expr.op}' membutuhkan dua angka", expr.span)
            if expr.op in ("==", "!="):
                if left == right or (left in NUMERIC and right in NUMERIC): return "bool"
                if self.is_assignable(left, right) or self.is_assignable(right, left): return "bool"
                raise RancageTypeError(f"Tidak bisa membandingkan {left} dengan {right}", expr.span)
            if expr.op in ("&&", "||"):
                if left == right == "bool": return "bool"
                raise RancageTypeError(f"Operator '{expr.op}' membutuhkan dua bool", expr.span)
        if isinstance(expr, Call):
            if expr.name == "len":
                if len(expr.args) != 1:
                    raise RancageTypeError(f"Fungsi 'len' membutuhkan 1 argumen, menerima {len(expr.args)}", expr.span)
                arg_t = self._expr(expr.args[0], env, None, consts)
                if arg_t == "string" or (arg_t.startswith("list[") and arg_t.endswith("]")) or (arg_t.startswith("map[string, ") and arg_t.endswith("]")):
                    return "int"
                raise RancageTypeError(f"Fungsi 'len' tidak mendukung argumen bertipe {arg_t}", expr.span)
            if expr.name == "push":
                if len(expr.args) != 2:
                    raise RancageTypeError(f"Fungsi 'push' membutuhkan 2 argumen, menerima {len(expr.args)}", expr.span)
                root = self._get_root_name(expr.args[0])
                if consts is not None and root is not None and root in consts:
                    raise RancageTypeError(f"Konstanta '{root}' tidak bisa diubah", expr.span)
                xs_t = self._expr(expr.args[0], env, None, consts)
                if not (xs_t.startswith("list[") and xs_t.endswith("]")):
                    raise RancageTypeError(f"Argumen pertama 'push' harus bertipe list, bukan {xs_t}", expr.span)
                elem_t = xs_t[5:-1]
                item_t = self._expr(expr.args[1], env, elem_t, consts)
                if not self.is_assignable(elem_t, item_t):
                    raise RancageTypeError(f"Argumen kedua 'push' harus bertipe {elem_t}, bukan {item_t}", expr.span)
                return "void"
            if expr.name == "pop":
                if len(expr.args) != 1:
                    raise RancageTypeError(f"Fungsi 'pop' membutuhkan 1 argumen, menerima {len(expr.args)}", expr.span)
                root = self._get_root_name(expr.args[0])
                if consts is not None and root is not None and root in consts:
                    raise RancageTypeError(f"Konstanta '{root}' tidak bisa diubah", expr.span)
                xs_t = self._expr(expr.args[0], env, None, consts)
                if not (xs_t.startswith("list[") and xs_t.endswith("]")):
                    raise RancageTypeError(f"Argumen 'pop' harus bertipe list, bukan {xs_t}", expr.span)
                return xs_t[5:-1]
            if expr.name == "ord":
                if len(expr.args) != 1:
                    raise RancageTypeError(f"Fungsi 'ord' membutuhkan 1 argumen, menerima {len(expr.args)}", expr.span)
                arg_t = self._expr(expr.args[0], env, None, consts)
                if arg_t != "string":
                    raise RancageTypeError(f"Argumen 'ord' harus bertipe string, bukan {arg_t}", expr.span)
                return "int"
            if expr.name == "chr":
                if len(expr.args) != 1:
                    raise RancageTypeError(f"Fungsi 'chr' membutuhkan 1 argumen, menerima {len(expr.args)}", expr.span)
                arg_t = self._expr(expr.args[0], env, None, consts)
                if arg_t != "int":
                    raise RancageTypeError(f"Argumen 'chr' harus bertipe int, bukan {arg_t}", expr.span)
                return "string"
            if expr.name == "slice":
                if len(expr.args) != 3:
                    raise RancageTypeError(f"Fungsi 'slice' membutuhkan 3 argumen, menerima {len(expr.args)}", expr.span)
                s_t = self._expr(expr.args[0], env, None, consts)
                start_t = self._expr(expr.args[1], env, None, consts)
                length_t = self._expr(expr.args[2], env, None, consts)
                if s_t != "string":
                    raise RancageTypeError(f"Argumen 1 'slice' harus bertipe string, bukan {s_t}", expr.span)
                if start_t != "int" or length_t != "int":
                    raise RancageTypeError("Argumen start dan length 'slice' harus bertipe int", expr.span)
                return "string"
            if expr.name == "map_has":
                if len(expr.args) != 2:
                    raise RancageTypeError(f"Fungsi 'map_has' membutuhkan 2 argumen, menerima {len(expr.args)}", expr.span)
                m_t = self._expr(expr.args[0], env, None, consts)
                k_t = self._expr(expr.args[1], env, None, consts)
                if not (m_t.startswith("map[string, ") and m_t.endswith("]")):
                    raise RancageTypeError(f"Argumen 1 'map_has' harus bertipe map, bukan {m_t}", expr.span)
                if k_t != "string":
                    raise RancageTypeError(f"Argumen 2 'map_has' harus bertipe string, bukan {k_t}", expr.span)
                return "bool"
            if expr.name == "map_remove":
                if len(expr.args) != 2:
                    raise RancageTypeError(f"Fungsi 'map_remove' membutuhkan 2 argumen, menerima {len(expr.args)}", expr.span)
                root = self._get_root_name(expr.args[0])
                if consts is not None and root is not None and root in consts:
                    raise RancageTypeError(f"Konstanta '{root}' tidak bisa diubah", expr.span)
                m_t = self._expr(expr.args[0], env, None, consts)
                k_t = self._expr(expr.args[1], env, None, consts)
                if not (m_t.startswith("map[string, ") and m_t.endswith("]")):
                    raise RancageTypeError(f"Argumen 1 'map_remove' harus bertipe map, bukan {m_t}", expr.span)
                if k_t != "string":
                    raise RancageTypeError(f"Argumen 2 'map_remove' harus bertipe string, bukan {k_t}", expr.span)
                return "bool"
            sig = self.signatures.get(expr.name)
            if sig is None:
                raise RancageTypeError(f"Fungsi '{expr.name}' tidak dikenal", expr.span)
            if len(expr.args) != len(sig.params):
                raise RancageTypeError(f"Fungsi '{expr.name}' membutuhkan {len(sig.params)} argumen, menerima {len(expr.args)}", expr.span)
            for i, (arg, expected_param) in enumerate(zip(expr.args, sig.params), start=1):
                actual = self._expr(arg, env, expected_param if expected_param != "any" else None, consts)
                if expected_param != "any" and not self.is_assignable(expected_param, actual):
                    raise RancageTypeError(f"Argumen {i} fungsi '{expr.name}' harus {expected_param}, bukan {actual}", expr.span)
            return sig.returns
        raise RancageTypeError("Ekspresi tidak didukung", getattr(expr, "span", Span(1, 1)))

def check_types(program: Program) -> None:
    TypeChecker(program).check()
