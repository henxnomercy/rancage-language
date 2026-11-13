"""Small, bounded NOVA bytecode virtual machine. No eval/exec or host imports."""
from __future__ import annotations
import json
import math
from pathlib import Path

class NovaRuntimeError(Exception): pass

OPS = {"PUSH", "LOAD", "STORE", "POP", "ADD", "SUB", "MUL", "DIV", "MOD", "EQ", "NE", "LT", "LE", "GT", "GE", "AND", "OR", "NOT", "NEG", "JUMP", "JUMP_IF_FALSE", "CALL", "RETURN"}

class VirtualMachine:
    def __init__(self, program: dict, output=print, max_steps: int = 1_000_000, max_depth: int = 128):
        self.program = program
        self.output = output
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.steps = 0
        self._validate()

    @classmethod
    def from_file(cls, path: str | Path, **kwargs) -> "VirtualMachine":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise NovaRuntimeError(f"Tidak bisa membaca bytecode: {exc}") from exc
        return cls(data, **kwargs)

    def _validate(self) -> None:
        if not isinstance(self.program, dict) or self.program.get("format") != "NOVA-IR" or self.program.get("version") != "0.1":
            raise NovaRuntimeError("Format atau versi NOVA-IR tidak didukung")
        functions = self.program.get("functions")
        if not isinstance(functions, dict) or self.program.get("entry") not in functions:
            raise NovaRuntimeError("Tabel fungsi atau entry point tidak valid")
        if len(functions) > 10_000:
            raise NovaRuntimeError("Bytecode memiliki terlalu banyak fungsi")
        for name, fn in functions.items():
            if not isinstance(name, str) or not name or not isinstance(fn, dict):
                raise NovaRuntimeError("Deklarasi fungsi bytecode tidak valid")
            params, code = fn.get("params"), fn.get("code")
            if (not isinstance(params, list) or not all(isinstance(p, str) and p for p in params)
                    or len(set(params)) != len(params) or not isinstance(code, list)):
                raise NovaRuntimeError(f"Metadata fungsi '{name}' tidak valid")
            if len(code) > 1_000_000:
                raise NovaRuntimeError(f"Fungsi '{name}' memiliki terlalu banyak instruksi")
            for instruction in code:
                if not isinstance(instruction, list) or not instruction or instruction[0] not in OPS:
                    raise NovaRuntimeError(f"Instruksi tidak dikenal dalam fungsi '{name}'")
                op = instruction[0]
                no_arg = OPS - {"PUSH", "LOAD", "STORE", "JUMP", "JUMP_IF_FALSE", "CALL"}
                if op in no_arg and len(instruction) != 1:
                    raise NovaRuntimeError(f"Arity instruksi {op} tidak valid")
                if op == "PUSH":
                    if len(instruction) != 2 or not (instruction[1] is None or type(instruction[1]) in (bool, int, float, str)):
                        raise NovaRuntimeError("Konstanta PUSH tidak valid")
                    if isinstance(instruction[1], float) and not math.isfinite(instruction[1]):
                        raise NovaRuntimeError("Konstanta float harus finite")
                if op in ("LOAD", "STORE"):
                    if len(instruction) != 2 or not isinstance(instruction[1], str) or not instruction[1]:
                        raise NovaRuntimeError(f"Operand {op} tidak valid")
                if op in ("JUMP", "JUMP_IF_FALSE"):
                    if len(instruction) != 2 or type(instruction[1]) is not int or not 0 <= instruction[1] <= len(code):
                        raise NovaRuntimeError(f"Target {op} tidak valid")
                if op == "CALL":
                    if (len(instruction) != 3 or not isinstance(instruction[1], str)
                            or type(instruction[2]) is not int or instruction[2] < 0
                            or (instruction[1] != "print" and instruction[1] not in functions)):
                        raise NovaRuntimeError("Operand CALL tidak valid")

    def run(self):
        entry = self.program["entry"]
        result = self._call(entry, [], 0)
        if result is None: return 0
        if isinstance(result, bool) or not isinstance(result, int):
            raise NovaRuntimeError("Fungsi main harus mengembalikan int atau void")
        return result

    def _call(self, name: str, args: list, depth: int):
        if name == "print":
            if len(args) != 1: raise NovaRuntimeError("print membutuhkan tepat satu argumen")
            self.output(self._format(args[0]))
            return None
        if depth >= self.max_depth:
            raise NovaRuntimeError("Batas kedalaman pemanggilan fungsi terlampaui")
        fn = self.program["functions"].get(name)
        if fn is None: raise NovaRuntimeError(f"Fungsi bytecode tidak ditemukan: {name}")
        params, code = fn["params"], fn["code"]
        if len(args) != len(params): raise NovaRuntimeError(f"Jumlah argumen fungsi '{name}' tidak sesuai")
        locals_ = dict(zip(params, args))
        stack = []
        ip = 0
        while ip < len(code):
            self.steps += 1
            if self.steps > self.max_steps:
                raise NovaRuntimeError("Batas instruksi program terlampaui")
            ins = code[ip]
            op = ins[0]
            try:
                if op == "PUSH": stack.append(ins[1])
                elif op == "LOAD":
                    if ins[1] not in locals_: raise NovaRuntimeError(f"Variabel runtime tidak ditemukan: {ins[1]}")
                    stack.append(locals_[ins[1]])
                elif op == "STORE":
                    locals_[ins[1]] = self._pop(stack)
                elif op == "POP": self._pop(stack)
                elif op == "JUMP":
                    self._check_jump(ins[1], len(code)); ip = ins[1]; continue
                elif op == "JUMP_IF_FALSE":
                    condition = self._pop(stack)
                    if not isinstance(condition, bool): raise NovaRuntimeError("Kondisi branch bukan boolean")
                    if not condition:
                        self._check_jump(ins[1], len(code)); ip = ins[1]; continue
                elif op == "CALL":
                    argc = ins[2]
                    if not isinstance(argc, int) or argc < 0 or len(stack) < argc: raise NovaRuntimeError("Instruksi CALL tidak valid")
                    call_args = stack[-argc:] if argc else []
                    if argc: del stack[-argc:]
                    stack.append(self._call(ins[1], call_args, depth + 1))
                elif op == "RETURN": return self._pop(stack)
                elif op == "NOT": stack.append(not self._require_bool(self._pop(stack)))
                elif op == "NEG": stack.append(-self._require_number(self._pop(stack)))
                else:
                    right, left = self._pop(stack), self._pop(stack)
                    stack.append(self._binary(op, left, right))
            except IndexError as exc:
                raise NovaRuntimeError(f"Stack underflow pada instruksi {ip} fungsi '{name}'") from exc
            except ZeroDivisionError as exc:
                raise NovaRuntimeError("Pembagian dengan nol") from exc
            ip += 1
        return None

    @staticmethod
    def _pop(stack):
        if not stack: raise NovaRuntimeError("Stack underflow")
        return stack.pop()

    @staticmethod
    def _check_jump(target, length):
        if not isinstance(target, int) or target < 0 or target > length:
            raise NovaRuntimeError("Target jump bytecode tidak valid")

    @staticmethod
    def _require_bool(value):
        if not isinstance(value, bool): raise NovaRuntimeError("Operasi membutuhkan boolean")
        return value

    @staticmethod
    def _require_number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise NovaRuntimeError("Operasi membutuhkan angka")
        return value

    def _binary(self, op, a, b):
        if op == "ADD":
            if isinstance(a, str) and isinstance(b, str): return a + b
            return self._require_number(a) + self._require_number(b)
        if op == "SUB": return self._require_number(a) - self._require_number(b)
        if op == "MUL": return self._require_number(a) * self._require_number(b)
        if op == "DIV": return self._require_number(a) / self._require_number(b)
        if op == "MOD": return self._require_number(a) % self._require_number(b)
        if op == "EQ":
            if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
                return a == b
            return type(a) is type(b) and a == b
        if op == "NE":
            if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
                return a != b
            return not (type(a) is type(b) and a == b)
        if op in ("LT", "LE", "GT", "GE"):
            a, b = self._require_number(a), self._require_number(b)
            return {"LT": a < b, "LE": a <= b, "GT": a > b, "GE": a >= b}[op]
        if op == "AND": return self._require_bool(a) and self._require_bool(b)
        if op == "OR": return self._require_bool(a) or self._require_bool(b)
        raise NovaRuntimeError(f"Opcode tidak didukung: {op}")

    @staticmethod
    def _format(value):
        if value is True: return "true"
        if value is False: return "false"
        if value is None: return "null"
        return str(value)
