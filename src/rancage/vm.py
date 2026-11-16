"""Small, bounded RANCAGE bytecode virtual machine. No eval/exec or host imports."""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any


class RancageRuntimeError(Exception):
    pass


MAX_STEPS = 1_000_000
MAX_DEPTH = 128
MAX_COLLECTION_SIZE = 100_000
MAX_STRING_LENGTH = 1_000_000
MAX_FUNCTIONS = 10_000
MAX_INSTRUCTIONS_PER_FN = 1_000_000

MAX_INTEGER_BITS = 64
MIN_INT64 = -(1 << 63)
MAX_INT64 = (1 << 63) - 1

MAX_ALLOCATED_UNITS = 2_000_000
MAX_FORMAT_DEPTH = 32


def format_value(value: Any, seen: set[int] | None = None, depth: int = 0) -> str:
    if depth > MAX_FORMAT_DEPTH:
        if isinstance(value, RecordInstance):
            return f"{value.name} {{...}}"
        if isinstance(value, list):
            return "[...]"
        if isinstance(value, dict):
            return "{...}"
        return "..."
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return f"'{value}'" if depth > 0 else value
    if isinstance(value, (int, float)):
        return str(value)

    seen = seen if seen is not None else set()
    obj_id = id(value)
    if obj_id in seen:
        return "<cycle>"

    seen.add(obj_id)
    try:
        if isinstance(value, RecordInstance):
            entries = [f"'{k}': {format_value(v, seen, depth + 1)}" for k, v in value.fields.items()]
            return f"{value.name} {{{', '.join(entries)}}}"
        if isinstance(value, list):
            entries = [format_value(v, seen, depth + 1) for v in value]
            return f"[{', '.join(entries)}]"
        if isinstance(value, dict):
            entries = [f"'{k}': {format_value(v, seen, depth + 1)}" for k, v in value.items()]
            return f"{{{', '.join(entries)}}}"
        return str(value)
    finally:
        seen.remove(obj_id)


class RecordInstance:
    __slots__ = ("name", "fields")

    def __init__(self, name: str, fields: dict[str, Any]):
        self.name = name
        self.fields = fields

    def __repr__(self) -> str:
        return format_value(self)

INTRINSICS = {
    "print": 1,
    "len": 1,
    "push": 2,
    "pop": 1,
    "ord": 1,
    "chr": 1,
    "slice": 3,
    "map_has": 2,
    "map_remove": 2,
}

STAGE0_OPS = {
    "MAKE_LIST",
    "LIST_GET",
    "LIST_SET",
    "MAKE_MAP",
    "MAP_GET",
    "MAP_SET",
    "MAKE_RECORD",
    "GET_FIELD",
    "SET_FIELD",
    "STRING_GET",
}

OPS = {
    "PUSH", "LOAD", "STORE", "POP", "ADD", "SUB", "MUL", "DIV", "MOD",
    "EQ", "NE", "LT", "LE", "GT", "GE", "AND", "OR", "NOT", "NEG",
    "JUMP", "JUMP_IF_FALSE", "CALL", "RETURN",
    *STAGE0_OPS,
}


class VirtualMachine:
    def __init__(
        self,
        program: dict,
        output=print,
        max_steps: int = MAX_STEPS,
        max_depth: int = MAX_DEPTH,
        max_allocated_units: int = MAX_ALLOCATED_UNITS,
    ):
        self.program = program
        self.output = output
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.max_allocated_units = max_allocated_units
        self.steps = 0
        self.allocated_units = 0
        self._validate()

    def _charge_allocation(self, units: int) -> None:
        if units < 0:
            raise RancageRuntimeError("Unit alokasi tidak valid")
        if self.allocated_units + units > self.max_allocated_units:
            raise RancageRuntimeError("Batas alokasi memori program terlampaui")
        self.allocated_units += units

    @classmethod
    def from_file(cls, path: str | Path, **kwargs) -> "VirtualMachine":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RancageRuntimeError(f"Tidak bisa membaca bytecode: {exc}") from exc
        return cls(data, **kwargs)

    def _validate(self) -> None:
        if not isinstance(self.program, dict) or self.program.get("format") not in {"RANCAGE-IR", "NOVA-IR"} or self.program.get("version") not in {"0.1", "0.2"}:
            raise RancageRuntimeError("Format atau versi RANCAGE-IR tidak didukung")
        functions = self.program.get("functions")
        if not isinstance(functions, dict) or self.program.get("entry") not in functions:
            raise RancageRuntimeError("Tabel fungsi atau entry point tidak valid")
        if len(functions) > MAX_FUNCTIONS:
            raise RancageRuntimeError("Bytecode memiliki terlalu banyak fungsi")

        records = self.program.get("records")
        if records is not None:
            if not isinstance(records, dict):
                raise RancageRuntimeError("Metadata records tidak valid")
            if len(records) > 10_000:
                raise RancageRuntimeError("Terlalu banyak tipe record")
            for rec_name, rec_meta in records.items():
                if not isinstance(rec_name, str) or not rec_name or not isinstance(rec_meta, dict):
                    raise RancageRuntimeError("Deklarasi record tidak valid")
                fields = rec_meta.get("fields")
                if not isinstance(fields, list):
                    raise RancageRuntimeError(f"Field record '{rec_name}' tidak valid")
                field_names = set()
                for f in fields:
                    if not isinstance(f, dict) or "name" not in f or "type" not in f:
                        raise RancageRuntimeError(f"Field definition record '{rec_name}' tidak valid")
                    fname = f["name"]
                    if not isinstance(fname, str) or not fname or fname in field_names:
                        raise RancageRuntimeError(f"Nama field '{fname}' tidak valid atau duplikat pada record '{rec_name}'")
                    field_names.add(fname)

        for name, fn in functions.items():
            if not isinstance(name, str) or not name or not isinstance(fn, dict):
                raise RancageRuntimeError("Deklarasi fungsi bytecode tidak valid")
            params, code = fn.get("params"), fn.get("code")
            if (not isinstance(params, list) or not all(isinstance(p, str) and p for p in params)
                    or len(set(params)) != len(params) or not isinstance(code, list)):
                raise RancageRuntimeError(f"Metadata fungsi '{name}' tidak valid")
            if len(code) > MAX_INSTRUCTIONS_PER_FN:
                raise RancageRuntimeError(f"Fungsi '{name}' memiliki terlalu banyak instruksi")
            for instruction in code:
                if not isinstance(instruction, list) or not instruction or instruction[0] not in OPS:
                    raise RancageRuntimeError(f"Instruksi tidak dikenal dalam fungsi '{name}'")
                op = instruction[0]
                no_arg = OPS - {"PUSH", "LOAD", "STORE", "JUMP", "JUMP_IF_FALSE", "CALL", "MAKE_LIST", "MAKE_MAP", "MAKE_RECORD", "GET_FIELD", "SET_FIELD"}
                if op in no_arg and len(instruction) != 1:
                    raise RancageRuntimeError(f"Arity instruksi {op} tidak valid")
                if op == "PUSH":
                    if len(instruction) != 2 or not (instruction[1] is None or type(instruction[1]) in (bool, int, float, str)):
                        raise RancageRuntimeError("Konstanta PUSH tidak valid")
                    cval = instruction[1]
                    if type(cval) is int and not (MIN_INT64 <= cval <= MAX_INT64):
                        raise RancageRuntimeError(f"Konstanta integer di luar batas 64-bit: {cval}")
                    if isinstance(cval, float) and not math.isfinite(cval):
                        raise RancageRuntimeError("Konstanta float harus finite")
                elif op in ("LOAD", "STORE"):
                    if len(instruction) != 2 or not isinstance(instruction[1], str) or not instruction[1]:
                        raise RancageRuntimeError(f"Operand {op} tidak valid")
                elif op in ("JUMP", "JUMP_IF_FALSE"):
                    if len(instruction) != 2 or type(instruction[1]) is not int or not 0 <= instruction[1] <= len(code):
                        raise RancageRuntimeError(f"Target {op} tidak valid")
                elif op == "CALL":
                    if (len(instruction) != 3 or not isinstance(instruction[1], str)
                            or type(instruction[2]) is not int or isinstance(instruction[2], bool) or instruction[2] < 0):
                        raise RancageRuntimeError("Operand CALL tidak valid")
                    callee = instruction[1]
                    argc = instruction[2]
                    if callee in INTRINSICS:
                        if argc != INTRINSICS[callee]:
                            raise RancageRuntimeError(f"Arity pemanggilan intrinsic '{callee}' tidak valid")
                    elif callee in functions:
                        fn_target = functions[callee]
                        if not isinstance(fn_target, dict):
                            raise RancageRuntimeError(f"Metadata fungsi target '{callee}' tidak valid")
                        fn_params = fn_target.get("params")
                        if not isinstance(fn_params, list):
                            raise RancageRuntimeError(f"Metadata parameter fungsi '{callee}' tidak valid")
                        if argc != len(fn_params):
                            raise RancageRuntimeError(
                                f"Arity pemanggilan fungsi '{callee}' tidak valid: diharapkan {len(fn_params)}, menerima {argc}"
                            )
                    else:
                        raise RancageRuntimeError(f"Fungsi target CALL '{callee}' tidak ditemukan")
                elif op in ("MAKE_LIST", "MAKE_MAP"):
                    if len(instruction) != 2 or type(instruction[1]) is not int or instruction[1] < 0:
                        raise RancageRuntimeError(f"Operand {op} tidak valid")
                elif op == "MAKE_RECORD":
                    if len(instruction) != 3 or not isinstance(instruction[1], str) or not isinstance(instruction[2], list):
                        raise RancageRuntimeError("Operand MAKE_RECORD tidak valid")
                    rec_name = instruction[1]
                    field_list = instruction[2]
                    if not records or rec_name not in records:
                        raise RancageRuntimeError(f"Tipe record '{rec_name}' tidak ditemukan pada metadata records")
                    expected_fields = [f["name"] for f in records[rec_name]["fields"]]
                    if (len(field_list) != len(expected_fields)
                            or sorted(field_list) != sorted(expected_fields)
                            or len(set(field_list)) != len(field_list)):
                        raise RancageRuntimeError(f"Field operand MAKE_RECORD tidak cocok dengan deklarasi record '{rec_name}'")
                elif op in ("GET_FIELD", "SET_FIELD"):
                    if len(instruction) != 2 or not isinstance(instruction[1], str) or not instruction[1]:
                        raise RancageRuntimeError(f"Operand {op} tidak valid")

    def run(self):
        entry = self.program["entry"]
        result = self._call(entry, [], 0)
        if result is None:
            return 0
        if isinstance(result, bool) or not isinstance(result, int):
            raise RancageRuntimeError("Fungsi main harus mengembalikan int atau void")
        return result

    def _call_intrinsic(self, name: str, args: list) -> Any:
        if name == "print":
            if len(args) != 1:
                raise RancageRuntimeError("print membutuhkan tepat satu argumen")
            self.output(self._format(args[0]))
            return None
        if name == "len":
            target = args[0]
            if target is None:
                raise RancageRuntimeError("Null reference dereference")
            if isinstance(target, (list, str)):
                return len(target)
            if isinstance(target, dict) and not isinstance(target, RecordInstance):
                return len(target)
            raise RancageRuntimeError(f"Fungsi len tidak mendukung tipe: {type(target).__name__}")
        if name == "push":
            target, item = args[0], args[1]
            if target is None:
                raise RancageRuntimeError("Null reference dereference")
            if type(target) is not list:
                raise RancageRuntimeError("Argumen pertama push harus bertipe list")
            if len(target) >= MAX_COLLECTION_SIZE:
                raise RancageRuntimeError("Batas kapasitas koleksi terlampaui")
            self._charge_allocation(1)
            target.append(item)
            return None
        if name == "pop":
            target = args[0]
            if target is None:
                raise RancageRuntimeError("Null reference dereference")
            if type(target) is not list:
                raise RancageRuntimeError("Argumen pop harus bertipe list")
            if not target:
                raise RancageRuntimeError("Operasi pop pada list kosong")
            return target.pop()
        if name == "ord":
            target = args[0]
            if target is None:
                raise RancageRuntimeError("Null reference dereference")
            if not isinstance(target, str):
                raise RancageRuntimeError("Argumen ord harus bertipe string")
            if len(target) != 1:
                raise RancageRuntimeError("Fungsi ord membutuhkan string tepat 1 karakter")
            return ord(target)
        if name == "chr":
            cp = args[0]
            if type(cp) is not int or isinstance(cp, bool):
                raise RancageRuntimeError("Argumen chr harus bertipe integer")
            if cp < 0 or (0xD800 <= cp <= 0xDFFF) or cp > 0x10FFFF:
                raise RancageRuntimeError(f"Code point Unicode tidak valid: {cp}")
            self._charge_allocation(1)
            return chr(cp)
        if name == "slice":
            target, start, length = args[0], args[1], args[2]
            if target is None:
                raise RancageRuntimeError("Null reference dereference")
            if not isinstance(target, str):
                raise RancageRuntimeError("Argumen 1 slice harus bertipe string")
            if type(start) is not int or isinstance(start, bool) or type(length) is not int or isinstance(length, bool):
                raise RancageRuntimeError("Argumen start dan length slice harus bertipe integer")
            if start < 0 or length < 0 or start > len(target):
                raise RancageRuntimeError("Argumen slice di luar batas yang valid")
            end = min(len(target), start + length)
            slice_len = end - start
            if slice_len > MAX_STRING_LENGTH:
                raise RancageRuntimeError("Batas panjang string terlampaui")
            self._charge_allocation(slice_len)
            result = target[start:end]
            return result
        if name == "map_has":
            target, key = args[0], args[1]
            if target is None:
                raise RancageRuntimeError("Null reference dereference")
            if type(target) is not dict or isinstance(target, RecordInstance):
                raise RancageRuntimeError("Argumen 1 map_has harus bertipe map")
            if not isinstance(key, str):
                raise RancageRuntimeError("Argumen 2 map_has harus bertipe string")
            return key in target
        if name == "map_remove":
            target, key = args[0], args[1]
            if target is None:
                raise RancageRuntimeError("Null reference dereference")
            if type(target) is not dict or isinstance(target, RecordInstance):
                raise RancageRuntimeError("Argumen 1 map_remove harus bertipe map")
            if not isinstance(key, str):
                raise RancageRuntimeError("Argumen 2 map_remove harus bertipe string")
            if key in target:
                del target[key]
                return True
            return False
        raise RancageRuntimeError(f"Intrinsic tidak dikenal: {name}")

    def _call(self, name: str, args: list, depth: int):
        if depth >= self.max_depth:
            raise RancageRuntimeError("Batas kedalaman pemanggilan fungsi terlampaui")
        fn = self.program["functions"].get(name)
        if fn is None:
            raise RancageRuntimeError(f"Fungsi bytecode tidak ditemukan: {name}")
        params, code = fn["params"], fn["code"]
        if len(args) != len(params):
            raise RancageRuntimeError(f"Jumlah argumen fungsi '{name}' tidak sesuai")
        locals_ = dict(zip(params, args))
        stack = []
        ip = 0
        while ip < len(code):
            self.steps += 1
            if self.steps > self.max_steps:
                raise RancageRuntimeError("Batas instruksi program terlampaui")
            ins = code[ip]
            op = ins[0]
            try:
                if op == "PUSH":
                    stack.append(ins[1])
                elif op == "LOAD":
                    if ins[1] not in locals_:
                        raise RancageRuntimeError(f"Variabel runtime tidak ditemukan: {ins[1]}")
                    stack.append(locals_[ins[1]])
                elif op == "STORE":
                    locals_[ins[1]] = self._pop(stack)
                elif op == "POP":
                    self._pop(stack)
                elif op == "JUMP":
                    self._check_jump(ins[1], len(code))
                    ip = ins[1]
                    continue
                elif op == "JUMP_IF_FALSE":
                    condition = self._pop(stack)
                    if not isinstance(condition, bool):
                        raise RancageRuntimeError("Kondisi branch bukan boolean")
                    if not condition:
                        self._check_jump(ins[1], len(code))
                        ip = ins[1]
                        continue
                elif op == "CALL":
                    callee = ins[1]
                    argc = ins[2]
                    if not isinstance(argc, int) or argc < 0 or len(stack) < argc:
                        raise RancageRuntimeError("Instruksi CALL tidak valid")
                    call_args = stack[-argc:] if argc else []
                    if argc:
                        del stack[-argc:]
                    if callee in INTRINSICS:
                        stack.append(self._call_intrinsic(callee, call_args))
                    else:
                        stack.append(self._call(callee, call_args, depth + 1))
                elif op == "RETURN":
                    return self._pop(stack)
                elif op == "NOT":
                    stack.append(not self._require_bool(self._pop(stack)))
                elif op == "NEG":
                    val = self._require_number(self._pop(stack))
                    if type(val) is int:
                        res = -val
                        if not (MIN_INT64 <= res <= MAX_INT64):
                            raise RancageRuntimeError("Integer overflow pada operasi negasi")
                        stack.append(res)
                    else:
                        stack.append(-val)
                elif op == "MAKE_LIST":
                    count = ins[1]
                    if len(stack) < count:
                        raise RancageRuntimeError(f"Stack underflow pada MAKE_LIST di fungsi '{name}'")
                    if count > MAX_COLLECTION_SIZE:
                        raise RancageRuntimeError("Batas kapasitas koleksi terlampaui")
                    self._charge_allocation(count + 1)
                    elements = stack[-count:] if count else []
                    if count:
                        del stack[-count:]
                    stack.append(elements)
                elif op == "LIST_GET":
                    index = self._pop(stack)
                    target = self._pop(stack)
                    if target is None:
                        raise RancageRuntimeError("Null reference dereference")
                    if type(target) is not list:
                        raise RancageRuntimeError("Operasi membutuhkan list")
                    if type(index) is not int or isinstance(index, bool):
                        raise RancageRuntimeError("Indeks list harus integer")
                    if index < 0 or index >= len(target):
                        raise RancageRuntimeError(f"Indeks list di luar batas: {index} (panjang {len(target)})")
                    stack.append(target[index])
                elif op == "LIST_SET":
                    value = self._pop(stack)
                    index = self._pop(stack)
                    target = self._pop(stack)
                    if target is None:
                        raise RancageRuntimeError("Null reference dereference")
                    if type(target) is not list:
                        raise RancageRuntimeError("Operasi membutuhkan list")
                    if type(index) is not int or isinstance(index, bool):
                        raise RancageRuntimeError("Indeks list harus integer")
                    if index < 0 or index >= len(target):
                        raise RancageRuntimeError(f"Indeks list di luar batas: {index} (panjang {len(target)})")
                    target[index] = value
                elif op == "MAKE_MAP":
                    count = ins[1]
                    total = 2 * count
                    if len(stack) < total:
                        raise RancageRuntimeError(f"Stack underflow pada MAKE_MAP di fungsi '{name}'")
                    if count > MAX_COLLECTION_SIZE:
                        raise RancageRuntimeError("Batas kapasitas koleksi terlampaui")
                    self._charge_allocation(count + 1)
                    raw = stack[-total:] if total else []
                    if total:
                        del stack[-total:]
                    m = {}
                    for i in range(0, total, 2):
                        k, v = raw[i], raw[i + 1]
                        if not isinstance(k, str):
                            raise RancageRuntimeError("Key map harus string")
                        m[k] = v
                    stack.append(m)
                elif op == "MAP_GET":
                    key = self._pop(stack)
                    target = self._pop(stack)
                    if target is None:
                        raise RancageRuntimeError("Null reference dereference")
                    if type(target) is not dict or isinstance(target, RecordInstance):
                        raise RancageRuntimeError("Operasi membutuhkan map")
                    if not isinstance(key, str):
                        raise RancageRuntimeError("Key map harus string")
                    if key not in target:
                        raise RancageRuntimeError(f"Key map tidak ditemukan: '{key}'")
                    stack.append(target[key])
                elif op == "MAP_SET":
                    value = self._pop(stack)
                    key = self._pop(stack)
                    target = self._pop(stack)
                    if target is None:
                        raise RancageRuntimeError("Null reference dereference")
                    if type(target) is not dict or isinstance(target, RecordInstance):
                        raise RancageRuntimeError("Operasi membutuhkan map")
                    if not isinstance(key, str):
                        raise RancageRuntimeError("Key map harus string")
                    if key not in target:
                        if len(target) >= MAX_COLLECTION_SIZE:
                            raise RancageRuntimeError("Batas kapasitas koleksi terlampaui")
                        self._charge_allocation(1)
                    target[key] = value
                elif op == "MAKE_RECORD":
                    rec_name, fields = ins[1], ins[2]
                    n = len(fields)
                    if len(stack) < n:
                        raise RancageRuntimeError(f"Stack underflow pada MAKE_RECORD di fungsi '{name}'")
                    self._charge_allocation(n + 1)
                    vals = stack[-n:] if n else []
                    if n:
                        del stack[-n:]
                    field_dict = dict(zip(fields, vals))
                    stack.append(RecordInstance(rec_name, field_dict))
                elif op == "GET_FIELD":
                    field = ins[1]
                    target = self._pop(stack)
                    if target is None:
                        raise RancageRuntimeError("Null reference dereference")
                    if not isinstance(target, RecordInstance):
                        raise RancageRuntimeError(f"Akses field '{field}' pada tipe non-record")
                    if field not in target.fields:
                        raise RancageRuntimeError(f"Field '{field}' tidak ditemukan pada record '{target.name}'")
                    stack.append(target.fields[field])
                elif op == "SET_FIELD":
                    field = ins[1]
                    value = self._pop(stack)
                    target = self._pop(stack)
                    if target is None:
                        raise RancageRuntimeError("Null reference dereference")
                    if not isinstance(target, RecordInstance):
                        raise RancageRuntimeError(f"Mutasi field '{field}' pada tipe non-record")
                    if field not in target.fields:
                        raise RancageRuntimeError(f"Field '{field}' tidak ditemukan pada record '{target.name}'")
                    target.fields[field] = value
                elif op == "STRING_GET":
                    index = self._pop(stack)
                    target = self._pop(stack)
                    if target is None:
                        raise RancageRuntimeError("Null reference dereference")
                    if not isinstance(target, str):
                        raise RancageRuntimeError("Operasi membutuhkan string")
                    if type(index) is not int or isinstance(index, bool):
                        raise RancageRuntimeError("Indeks string harus integer")
                    if index < 0 or index >= len(target):
                        raise RancageRuntimeError(f"Indeks string di luar batas: {index} (panjang {len(target)})")
                    self._charge_allocation(1)
                    stack.append(target[index])
                else:
                    right, left = self._pop(stack), self._pop(stack)
                    stack.append(self._binary(op, left, right))
            except RancageRuntimeError:
                raise
            except IndexError as exc:
                raise RancageRuntimeError(f"Stack underflow pada instruksi {ip} fungsi '{name}'") from exc
            except ZeroDivisionError as exc:
                raise RancageRuntimeError("Pembagian dengan nol") from exc
            except Exception as exc:
                raise RancageRuntimeError(f"Runtime error pada instruksi {ip} ({op}) fungsi '{name}': {exc}") from exc
            ip += 1
        return None

    @staticmethod
    def _pop(stack: list) -> Any:
        if not stack:
            raise RancageRuntimeError("Stack underflow")
        return stack.pop()

    @staticmethod
    def _check_jump(target: int, length: int) -> None:
        if not isinstance(target, int) or target < 0 or target > length:
            raise RancageRuntimeError("Target jump bytecode tidak valid")

    @staticmethod
    def _require_bool(value: Any) -> bool:
        if not isinstance(value, bool):
            raise RancageRuntimeError("Operasi membutuhkan boolean")
        return value

    @staticmethod
    def _require_number(value: Any) -> int | float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RancageRuntimeError("Operasi membutuhkan angka")
        return value

    def _binary(self, op: str, a: Any, b: Any) -> Any:
        if op == "ADD":
            if isinstance(a, str) and isinstance(b, str):
                new_len = len(a) + len(b)
                if new_len > MAX_STRING_LENGTH:
                    raise RancageRuntimeError("Batas panjang string terlampaui")
                self._charge_allocation(new_len)
                return a + b
            val_a = self._require_number(a)
            val_b = self._require_number(b)
            res = val_a + val_b
            if type(res) is int and not (MIN_INT64 <= res <= MAX_INT64):
                raise RancageRuntimeError("Integer overflow pada operasi penjumlahan")
            return res
        if op == "SUB":
            val_a = self._require_number(a)
            val_b = self._require_number(b)
            res = val_a - val_b
            if type(res) is int and not (MIN_INT64 <= res <= MAX_INT64):
                raise RancageRuntimeError("Integer overflow pada operasi pengurangan")
            return res
        if op == "MUL":
            val_a = self._require_number(a)
            val_b = self._require_number(b)
            res = val_a * val_b
            if type(res) is int and not (MIN_INT64 <= res <= MAX_INT64):
                raise RancageRuntimeError("Integer overflow pada operasi perkalian")
            return res
        if op == "DIV":
            return self._require_number(a) / self._require_number(b)
        if op == "MOD":
            val_a = self._require_number(a)
            val_b = self._require_number(b)
            res = val_a % val_b
            if type(res) is int and not (MIN_INT64 <= res <= MAX_INT64):
                raise RancageRuntimeError("Integer overflow pada operasi modulo")
            return res
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
        if op == "AND":
            return self._require_bool(a) and self._require_bool(b)
        if op == "OR":
            return self._require_bool(a) or self._require_bool(b)
        raise RancageRuntimeError(f"Opcode tidak didukung: {op}")

    @staticmethod
    def _format(value: Any) -> str:
        return format_value(value)
