import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from rancage.ast import (
    Binary,
    ExprStmt,
    FieldAccess,
    FieldAssign,
    FieldDecl,
    FieldInit,
    Function,
    IndexAssign,
    IndexExpr,
    ListLiteral,
    Literal,
    MapLiteral,
    Name,
    NullLiteral,
    Program,
    RecordDecl,
    RecordInit,
    Span,
)
from rancage import __version__
from rancage.compiler import compile_program, Compiler, RancageCompilerError
from rancage.cli import main as cli_main
from rancage.lexer import Lexer, RancageSyntaxError, KEYWORDS, RESERVED
from rancage.parser import parse_source
from rancage.typesys import RancageTypeError, check_types
from rancage.vm import (
    RancageRuntimeError,
    VirtualMachine,
    RecordInstance,
    MAX_COLLECTION_SIZE,
    MAX_STRING_LENGTH,
    MIN_INT64,
    MAX_INT64,
    format_value,
)


def compile_text(source):
    program = parse_source(source)
    check_types(program)
    return compile_program(program)


class RancageLanguageTests(unittest.TestCase):
    def run_source(self, source):
        output = []
        ir = compile_text(source)
        code = VirtualMachine(ir, output=output.append).run()
        return output, code, ir

    def test_hello(self):
        out, code, _ = self.run_source('fn main() -> int { print("hello"); return 0; }')
        self.assertEqual(out, ["hello"])
        self.assertEqual(code, 0)

    def test_functions(self):
        out, _, _ = self.run_source('fn double(x: int) -> int { return x * 2; } fn main() -> int { print(double(21)); return 0; }')
        self.assertEqual(out, ["42"])

    def test_loop_and_branch(self):
        src = '''fn main() -> int {
            let x: int = 0;
            while (x < 3) { print(x); x = x + 1; }
            if (x == 3) { print("yes"); } else { print("no"); }
            return 0;
        }'''
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["0", "1", "2", "yes"])

    def test_type_error(self):
        with self.assertRaises(RancageTypeError):
            compile_text('fn main() -> int { let x: int = "wrong"; return 0; }')

    def test_const_cannot_be_assigned(self):
        with self.assertRaises(RancageTypeError):
            compile_text('fn main() -> int { const x: int = 1; x = 2; return 0; }')

    def test_division_by_zero(self):
        ir = compile_text('fn main() -> int { let x: float = 1.0 / 0.0; print(x); return 0; }')
        with self.assertRaises(RancageRuntimeError):
            VirtualMachine(ir, output=lambda _: None).run()

    def test_bytecode_roundtrip(self):
        ir = compile_text('fn main() -> int { print("roundtrip"); return 0; }')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "program.rcb"
            path.write_text(json.dumps(ir), encoding="utf-8")
            out = []
            vm = VirtualMachine.from_file(path, output=out.append)
            self.assertEqual(vm.run(), 0)
            self.assertEqual(out, ["roundtrip"])

    def test_nonvoid_must_return(self):
        with self.assertRaises(RancageTypeError):
            compile_text('fn main() -> int { let x: int = 2; }')

    def test_nested_variable_shadowing_is_rejected(self):
        source = '''fn main() -> int {
            let x: int = 1;
            if (true) { let x: int = 2; }
            print(x);
            return 0;
        }'''
        with self.assertRaises(RancageTypeError):
            compile_text(source)

    def test_execution_budget(self):
        ir = compile_text('fn main() -> int { while (true) { print(1); } return 0; }')
        with self.assertRaises(RancageRuntimeError):
            VirtualMachine(ir, output=lambda _: None, max_steps=20).run()

    def test_mixed_numeric_equality(self):
        out, _, _ = self.run_source('fn main() -> int { print(1 == 1.0); return 0; }')
        self.assertEqual(out, ["true"])

    def test_cli_uses_cage_and_rcb_as_canonical_extensions(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "hello.cage"
            source.write_text('fn main() -> int { print("cli"); return 0; }', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["check", str(source)]), 0)
                self.assertEqual(cli_main(["build", str(source)]), 0)
            bytecode = source.with_suffix(".rcb")
            self.assertTrue(bytecode.exists())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(cli_main(["run", str(bytecode)]), 0)
            self.assertIn("cli", output.getvalue())

    def test_cli_rejects_old_file_extensions(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli_main(["run", "old.nvm"]), 2)
            self.assertEqual(cli_main(["run", "old.nova"]), 2)
            self.assertEqual(cli_main(["run", "old.rcg"]), 2)
            self.assertEqual(cli_main(["check", "old.rcg"]), 2)
            self.assertEqual(cli_main(["build", "old.nova"]), 2)

    def test_legacy_nova_ir_payload_is_still_readable(self):
        ir = compile_text('fn main() -> int { print("legacy"); return 0; }')
        ir["format"] = "NOVA-IR"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.rcb"
            path.write_text(json.dumps(ir), encoding="utf-8")
            out = []
            vm = VirtualMachine.from_file(path, output=out.append)
            self.assertEqual(vm.run(), 0)
            self.assertEqual(out, ["legacy"])

    def test_invalid_opcode_is_rejected(self):
        bad = {"format": "RANCAGE-IR", "version": "0.1", "entry": "main",
               "functions": {"main": {"params": [], "code": [["HOST_EXEC", "print(1)"]]}}}
        with self.assertRaises(RancageRuntimeError):
            VirtualMachine(bad)

    def test_unknown_character(self):
        with self.assertRaises(RancageSyntaxError):
            parse_source('fn main() -> int { @ return 0; }')


class Stage0Milestone01Tests(unittest.TestCase):
    def test_lexer_stage0_tokens(self):
        source = "record null [ ] . ?"
        tokens = Lexer(source).tokenize()
        kinds = [(tok.kind, tok.value) for tok in tokens]
        expected = [
            ("IDENT", "record"),
            ("IDENT", "null"),
            ("SYMBOL", "["),
            ("SYMBOL", "]"),
            ("SYMBOL", "."),
            ("SYMBOL", "?"),
            ("EOF", ""),
        ]
        self.assertEqual(kinds, expected)
        self.assertIn("record", KEYWORDS)
        self.assertIn("record", RESERVED)
        self.assertIn("null", RESERVED)

    def test_parser_rejects_keywords_as_identifiers(self):
        with self.assertRaises(RancageSyntaxError):
            parse_source("fn main() -> int { let record: int = 1; return 0; }")
        with self.assertRaises(RancageSyntaxError):
            parse_source("fn main() -> int { let null: int = 1; return 0; }")
        with self.assertRaises(RancageSyntaxError):
            parse_source("fn main() -> int { null = 1; return 0; }")
        with self.assertRaises(RancageSyntaxError):
            parse_source("fn main() -> int { record = 1; return 0; }")
        with self.assertRaises(RancageSyntaxError):
            parse_source("fn main() -> int { let x: int = record + 1; return 0; }")

    def test_ast_node_construction(self):
        span = Span(1, 1)
        f_decl = FieldDecl("x", "int", span)
        rec_decl = RecordDecl("Point", [f_decl], span)
        prog = Program(functions=[], module="main", records=[rec_decl])
        self.assertEqual(len(prog.records), 1)
        self.assertEqual(prog.records[0].name, "Point")

        null_lit = NullLiteral(span)
        self.assertIsNone(null_lit.value)
        self.assertEqual(null_lit.type_name, "null")

        name_node = Name("p", span)
        f_access = FieldAccess(name_node, "x", span)
        self.assertEqual(f_access.field, "x")
        self.assertEqual(f_access.target, name_node)

        idx_expr = IndexExpr(name_node, null_lit, span)
        self.assertEqual(idx_expr.target, name_node)
        self.assertEqual(idx_expr.index, null_lit)

        list_lit = ListLiteral([name_node], span)
        self.assertEqual(list_lit.elements, [name_node])

        f_init = FieldInit("x", name_node, span)
        rec_init = RecordInit("Point", [f_init], span)
        self.assertEqual(rec_init.name, "Point")

        map_lit = MapLiteral([(name_node, null_lit)], span)
        self.assertEqual(len(map_lit.entries), 1)

        f_assign = FieldAssign(name_node, "x", null_lit, span)
        self.assertEqual(f_assign.field, "x")

        idx_assign = IndexAssign(name_node, name_node, null_lit, span)
        self.assertEqual(idx_assign.value, null_lit)

    def test_field_access_and_index_parsing(self):
        src = "fn main() -> int { let a = p.x; let b = p.x.y; let c = items[0]; let d = p.items[0].val; return 0; }"
        prog = parse_source(src)
        body = prog.functions[0].body
        # let a = p.x
        self.assertIsInstance(body[0].value, FieldAccess)
        self.assertEqual(body[0].value.field, "x")
        self.assertEqual(body[0].value.target.value, "p")
        # let b = p.x.y
        self.assertIsInstance(body[1].value, FieldAccess)
        self.assertEqual(body[1].value.field, "y")
        self.assertIsInstance(body[1].value.target, FieldAccess)
        self.assertEqual(body[1].value.target.field, "x")
        # let c = items[0]
        self.assertIsInstance(body[2].value, IndexExpr)
        self.assertEqual(body[2].value.target.value, "items")
        self.assertEqual(body[2].value.index.value, 0)
        # let d = p.items[0].val
        self.assertIsInstance(body[3].value, FieldAccess)
        self.assertEqual(body[3].value.field, "val")
        self.assertIsInstance(body[3].value.target, IndexExpr)
        self.assertEqual(body[3].value.target.target.field, "items")

    def test_null_and_list_literal_parsing(self):
        src = "fn main() -> int { let n = null; let xs = [1, 2]; let empty = []; return 0; }"
        prog = parse_source(src)
        body = prog.functions[0].body
        self.assertIsInstance(body[0].value, NullLiteral)
        self.assertIsInstance(body[1].value, ListLiteral)
        self.assertEqual(len(body[1].value.elements), 2)
        self.assertIsInstance(body[2].value, ListLiteral)
        self.assertEqual(len(body[2].value.elements), 0)

    def test_chained_indexing_and_mixed_expressions(self):
        src = "fn main() -> int { let x = a[i][j]; let y = p.x + p.y; return 0; }"
        prog = parse_source(src)
        body = prog.functions[0].body
        # let x = a[i][j]
        self.assertIsInstance(body[0].value, IndexExpr)
        self.assertEqual(body[0].value.index.value, "j")
        self.assertIsInstance(body[0].value.target, IndexExpr)
        self.assertEqual(body[0].value.target.index.value, "i")
        self.assertEqual(body[0].value.target.target.value, "a")
        # span on outer IndexExpr should anchor to second '[' (line 1, col 32)
        self.assertEqual(body[0].value.span.column, 32)
        # let y = p.x + p.y
        self.assertIsInstance(body[1].value, Binary)
        self.assertEqual(body[1].value.op, "+")
        self.assertIsInstance(body[1].value.left, FieldAccess)
        self.assertEqual(body[1].value.left.field, "x")
        self.assertIsInstance(body[1].value.right, FieldAccess)
        self.assertEqual(body[1].value.right.field, "y")


class Stage0Milestone02Tests(unittest.TestCase):
    def check_source(self, source: str):
        prog = parse_source(source)
        check_types(prog)
        return prog

    def test_record_declaration_and_instantiation(self):
        src = """
        record Point {
            x: int;
            y: int;
        }
        record Node {
            val: int;
            next: Node?;
        }
        fn main() -> int {
            let p: Point = Point { x: 1, y: 2 };
            let px: int = p.x;
            let leaf: Node = Node { val: 2, next: null };
            let root: Node = Node { val: 1, next: leaf };
            return px;
        }
        """
        prog = self.check_source(src)
        self.assertEqual(len(prog.records), 2)
        self.assertEqual(prog.records[0].name, "Point")
        self.assertEqual(prog.records[1].name, "Node")

    def test_record_typecheck_errors(self):
        # duplicate record
        with self.assertRaises(RancageTypeError):
            self.check_source("record A { x: int; } record A { y: int; } fn main() -> int { return 0; }")
        # record name primitive collision
        with self.assertRaises(RancageTypeError):
            self.check_source("record int { x: int; } fn main() -> int { return 0; }")
        # duplicate field in declaration
        with self.assertRaises(RancageTypeError):
            self.check_source("record A { x: int; x: int; } fn main() -> int { return 0; }")
        # invalid field type
        with self.assertRaises(RancageTypeError):
            self.check_source("record A { x: unknown; } fn main() -> int { return 0; }")
        # unknown record init
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let x = Unknown { a: 1 }; return 0; }")
        # missing field in init
        with self.assertRaises(RancageTypeError):
            self.check_source("record Point { x: int; y: int; } fn main() -> int { let p = Point { x: 1 }; return 0; }")
        # unknown field in init
        with self.assertRaises(RancageTypeError):
            self.check_source("record Point { x: int; } fn main() -> int { let p = Point { x: 1, z: 2 }; return 0; }")
        # duplicate field in init
        with self.assertRaises(RancageTypeError):
            self.check_source("record Point { x: int; } fn main() -> int { let p = Point { x: 1, x: 2 }; return 0; }")
        # field type mismatch in init
        with self.assertRaises(RancageTypeError):
            self.check_source('record Point { x: int; } fn main() -> int { let p = Point { x: "no" }; return 0; }')
        # field access on non-record
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let n: int = 10; let x = n.val; return 0; }")
        # unknown field access on record
        with self.assertRaises(RancageTypeError):
            self.check_source("record Point { x: int; } fn main() -> int { let p = Point { x: 1 }; let z = p.z; return 0; }")

    def test_generic_collections_and_literals(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [1, 2, 3];
            let first: int = xs[0];
            let nested: list[list[int]] = [[1, 2], [3, 4]];
            let empty: list[string] = [];
            let s: string = "hello";
            let ch: string = s[0];
            let m: map[string, int] = {"a": 1, "b": 2};
            let empty_map: map[string, int] = {};
            let val: int = m["a"];
            return first;
        }
        """
        self.check_source(src)

    def test_generic_collections_typecheck_errors(self):
        # heterogeneous list
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { let xs = [1, "two", 3]; return 0; }')
        # empty list without type annotation
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let xs = []; return 0; }")
        # empty map without type annotation
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let m = {}; return 0; }")
        # non-string map key
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let m: map[string, int] = {1: 2}; return 0; }")
        # invalid index type on list
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { let xs: list[int] = [1]; let x = xs["bad"]; return 0; }')
        # invalid index type on string
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { let s: string = "a"; let c = s["bad"]; return 0; }')
        # indexing non-indexable type
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let n: int = 10; let x = n[0]; return 0; }")

    def test_nullability_and_equality(self):
        src = """
        record Box { val: int; }
        fn main() -> int {
            let b: Box? = null;
            let is_null: bool = b == null;
            let not_null: bool = b != null;
            let b2: Box? = Box { val: 42 };
            let same: bool = b == b2;
            let opt_i: int? = 10;
            let opt_null: int? = null;
            let cmp: bool = opt_i == opt_null;
            return 0;
        }
        """
        self.check_source(src)

        # null without type annotation
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let x = null; return 0; }")
        # null assigned to non-nullable
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let x: int = null; return 0; }")
        # nullable assigned to non-nullable
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let a: int? = 1; let b: int = a; return 0; }")
        # non-nullable compared with null
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let x: int = 1; let c = x == null; return 0; }")

    def test_target_assignments_and_const_preservation(self):
        src = """
        record Point { x: int; y: int; }
        fn main() -> int {
            let p: Point = Point { x: 1, y: 2 };
            p.x = 10;
            let xs: list[int] = [1, 2];
            xs[0] = 42;
            let m: map[string, int] = {"a": 1};
            m["a"] = 100;
            return p.x;
        }
        """
        self.check_source(src)

        # mutating const record field
        with self.assertRaises(RancageTypeError):
            self.check_source("record Point { x: int; } fn main() -> int { const p: Point = Point { x: 1 }; p.x = 2; return 0; }")
        # mutating const list index
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { const xs: list[int] = [1, 2]; xs[0] = 5; return 0; }")
        # mutating const map key
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { const m: map[string, int] = {"a": 1}; m["a"] = 2; return 0; }')
        # assigning to string index rejected (immutable)
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { let s: string = "hello"; s[0] = "H"; return 0; }')
        # field assign type mismatch
        with self.assertRaises(RancageTypeError):
            self.check_source('record Point { x: int; } fn main() -> int { let p: Point = Point { x: 1 }; p.x = "bad"; return 0; }')
        # list index assign type mismatch
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { let xs: list[int] = [1]; xs[0] = "bad"; return 0; }')
        # invalid assignment target (literal)
        with self.assertRaises(RancageSyntaxError):
            self.check_source("fn main() -> int { 1 = 2; return 0; }")

    def test_intrinsics_signatures(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [1, 2, 3];
            let n_list: int = len(xs);
            push(xs, 4);
            let popped: int = pop(xs);
            let s: string = "hello";
            let n_str: int = len(s);
            let code: int = ord(s);
            let ch: string = chr(65);
            let sub: string = slice(s, 1, 3);
            let m: map[string, int] = {"k": 1};
            let n_map: int = len(m);
            let has_k: bool = map_has(m, "k");
            let removed: bool = map_remove(m, "k");
            return 0;
        }
        """
        self.check_source(src)

        # len invalid arg
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { let x = len(10); return 0; }")
        # push invalid target
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { push(10, 1); return 0; }")
        # push element type mismatch
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { let xs: list[int] = [1]; push(xs, "bad"); return 0; }')
        # ord arg mismatch
        with self.assertRaises(RancageTypeError):
            self.check_source("fn main() -> int { ord(10); return 0; }")
        # chr arg mismatch
        with self.assertRaises(RancageTypeError):
            self.check_source('fn main() -> int { chr("bad"); return 0; }')

    def test_const_mutating_intrinsics_and_depth_limits(self):
        # non-mutating intrinsics on const are allowed
        ok_src = """
        fn main() -> int {
            const xs: list[int] = [1, 2, 3];
            let n_list: int = len(xs);
            const m: map[string, int] = {"a": 1};
            let has_a: bool = map_has(m, "a");
            const s: string = "hello";
            let n_str: int = len(s);
            let code: int = ord(s);
            let sub: string = slice(s, 0, 2);
            return 0;
        }
        """
        self.check_source(ok_src)

        # push on const list
        with self.assertRaises(RancageTypeError) as ctx:
            self.check_source("fn main() -> int { const xs: list[int] = [1, 2]; push(xs, 3); return 0; }")
        self.assertIn("Konstanta 'xs' tidak bisa diubah", str(ctx.exception))

        # pop on const list
        with self.assertRaises(RancageTypeError) as ctx:
            self.check_source("fn main() -> int { const xs: list[int] = [1, 2]; pop(xs); return 0; }")
        self.assertIn("Konstanta 'xs' tidak bisa diubah", str(ctx.exception))

        # map_remove on const map
        with self.assertRaises(RancageTypeError) as ctx:
            self.check_source('fn main() -> int { const m: map[string, int] = {"k": 1}; map_remove(m, "k"); return 0; }')
        self.assertIn("Konstanta 'm' tidak bisa diubah", str(ctx.exception))

        # mutating intrinsic on record field rooted in const
        with self.assertRaises(RancageTypeError) as ctx:
            self.check_source("""
            record Box { xs: list[int]; }
            fn main() -> int {
                const b: Box = Box { xs: [1, 2] };
                push(b.xs, 3);
                return 0;
            }
            """)
        self.assertIn("Konstanta 'b' tidak bisa diubah", str(ctx.exception))

        # generic type nesting within depth limit (64 levels)
        deep_type_64 = ("list[" * 64) + "int" + ("]" * 64)
        src_deep_ok = f"fn dummy(x: {deep_type_64}) -> int {{ return 0; }} fn main() -> int {{ return 0; }}"
        self.check_source(src_deep_ok)

        # generic type nesting exceeding depth limit (65 levels)
        deep_type_65 = ("list[" * 65) + "int" + ("]" * 65)
        src_deep_exceeded = f"fn dummy(x: {deep_type_65}) -> int {{ return 0; }} fn main() -> int {{ return 0; }}"
        with self.assertRaises(RancageSyntaxError) as ctx:
            self.check_source(src_deep_exceeded)
        self.assertIn("Batas kedalaman tipe terlampaui", str(ctx.exception))


class Stage0Milestone03Tests(unittest.TestCase):
    def test_make_list_emission(self):
        src = "fn main() -> int { let xs: list[int] = [10, 20, 30]; let ys: list[int] = []; return 0; }"
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["MAKE_LIST", 3], code)
        self.assertIn(["MAKE_LIST", 0], code)
        idx = code.index(["MAKE_LIST", 3])
        self.assertEqual(code[idx - 3 : idx], [["PUSH", 10], ["PUSH", 20], ["PUSH", 30]])
        self.assertEqual(code[idx + 1], ["STORE", "xs"])

    def test_list_get_and_set_emission(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [1, 2];
            let x: int = xs[0];
            xs[1] = 42;
            return 0;
        }
        """
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["LIST_GET"], code)
        self.assertIn(["LIST_SET"], code)
        get_idx = code.index(["LIST_GET"])
        self.assertEqual(code[get_idx - 2 : get_idx], [["LOAD", "xs"], ["PUSH", 0]])
        set_idx = code.index(["LIST_SET"])
        self.assertEqual(code[set_idx - 3 : set_idx], [["LOAD", "xs"], ["PUSH", 1], ["PUSH", 42]])

    def test_make_map_emission(self):
        src = 'fn main() -> int { let m: map[string, int] = {"a": 1, "b": 2}; let empty: map[string, int] = {}; return 0; }'
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["MAKE_MAP", 2], code)
        self.assertIn(["MAKE_MAP", 0], code)
        idx = code.index(["MAKE_MAP", 2])
        self.assertEqual(code[idx - 4 : idx], [["PUSH", "a"], ["PUSH", 1], ["PUSH", "b"], ["PUSH", 2]])
        self.assertEqual(code[idx + 1], ["STORE", "m"])

    def test_map_get_and_set_emission(self):
        src = """
        fn main() -> int {
            let m: map[string, int] = {"a": 1};
            let val: int = m["a"];
            m["a"] = 99;
            return 0;
        }
        """
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["MAP_GET"], code)
        self.assertIn(["MAP_SET"], code)
        get_idx = code.index(["MAP_GET"])
        self.assertEqual(code[get_idx - 2 : get_idx], [["LOAD", "m"], ["PUSH", "a"]])
        set_idx = code.index(["MAP_SET"])
        self.assertEqual(code[set_idx - 3 : set_idx], [["LOAD", "m"], ["PUSH", "a"], ["PUSH", 99]])

    def test_make_record_emission(self):
        src = """
        record Point { x: int; y: int; }
        fn main() -> int {
            let p: Point = Point { x: 10, y: 20 };
            return 0;
        }
        """
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["MAKE_RECORD", "Point", ["x", "y"]], code)
        idx = code.index(["MAKE_RECORD", "Point", ["x", "y"]])
        self.assertEqual(code[idx - 2 : idx], [["PUSH", 10], ["PUSH", 20]])
        self.assertEqual(code[idx + 1], ["STORE", "p"])

    def test_record_field_get_and_set_emission(self):
        src = """
        record Point { x: int; y: int; }
        fn main() -> int {
            let p: Point = Point { x: 10, y: 20 };
            let px: int = p.x;
            p.x = 50;
            return 0;
        }
        """
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["GET_FIELD", "x"], code)
        self.assertIn(["SET_FIELD", "x"], code)
        get_idx = code.index(["GET_FIELD", "x"])
        self.assertEqual(code[get_idx - 1], ["LOAD", "p"])
        set_idx = code.index(["SET_FIELD", "x"])
        self.assertEqual(code[set_idx - 2 : set_idx], [["LOAD", "p"], ["PUSH", 50]])

    def test_string_get_emission(self):
        src = 'fn main() -> int { let s: string = "hello"; let ch: string = s[0]; return 0; }'
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["STRING_GET"], code)
        idx = code.index(["STRING_GET"])
        self.assertEqual(code[idx - 2 : idx], [["LOAD", "s"], ["PUSH", 0]])
        self.assertEqual(code[idx + 1], ["STORE", "ch"])

    def test_null_literal_emission(self):
        src = "fn main() -> int { let n: int? = null; if (n == null) { return 0; } return 1; }"
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["PUSH", None], code)

    def test_intrinsics_call_emission(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [1, 2];
            let l: int = len(xs);
            let p: int = pop(xs);
            let o: int = ord("A");
            let c: string = chr(65);
            let sl: string = slice("abc", 0, 1);
            let m: map[string, int] = {"k": 1};
            let h: bool = map_has(m, "k");
            let r: bool = map_remove(m, "k");
            return 0;
        }
        """
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        self.assertIn(["CALL", "len", 1], code)
        self.assertIn(["CALL", "pop", 1], code)
        self.assertIn(["CALL", "ord", 1], code)
        self.assertIn(["CALL", "chr", 1], code)
        self.assertIn(["CALL", "slice", 3], code)
        self.assertIn(["CALL", "map_has", 2], code)
        self.assertIn(["CALL", "map_remove", 2], code)

    def test_expr_stmt_pop_stack_contract(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [1, 2];
            push(xs, 3);
            pop(xs);
            return 0;
        }
        """
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        push_idx = code.index(["CALL", "push", 2])
        self.assertEqual(code[push_idx + 1], ["POP"])
        pop_idx = code.index(["CALL", "pop", 1])
        self.assertEqual(code[pop_idx + 1], ["POP"])

    def test_ir_0_2_schema_and_metadata(self):
        src = """
        record User { id: int; name: string; }
        fn main() -> int {
            let u: User = User { id: 1, name: "Alice" };
            return 0;
        }
        """
        ir = compile_text(src)
        self.assertEqual(ir["format"], "RANCAGE-IR")
        self.assertEqual(ir["version"], "0.2")
        self.assertEqual(ir["entry"], "main")
        self.assertIn("records", ir)
        self.assertIn("User", ir["records"])
        self.assertEqual(
            ir["records"]["User"]["fields"],
            [{"name": "id", "type": "int"}, {"name": "name", "type": "string"}],
        )
        self.assertIn("main", ir["functions"])

    def test_missing_type_metadata_raises_compiler_error(self):
        span = Span(1, 1)
        raw_index_expr = IndexExpr(
            target=Name(value="xs", span=span),
            index=Literal(value=0, type_name="int", span=span),
            span=span,
        )
        stmt = ExprStmt(value=raw_index_expr, span=span)
        fn = Function(name="main", params=[], return_type="int", body=[stmt], span=span)
        prog = Program(module="test", records=[], functions=[fn])
        with self.assertRaises(RancageCompilerError) as ctx:
            Compiler(prog).compile()
        self.assertIn("Indexing expression requires inferred type metadata", str(ctx.exception))

        raw_index_assign = IndexAssign(
            target=Name(value="xs", span=span),
            index=Literal(value=0, type_name="int", span=span),
            value=Literal(value=1, type_name="int", span=span),
            span=span,
        )
        fn_assign = Function(name="main", params=[], return_type="int", body=[raw_index_assign], span=span)
        prog_assign = Program(module="test", records=[], functions=[fn_assign])
        with self.assertRaises(RancageCompilerError) as ctx:
            Compiler(prog_assign).compile()
        self.assertIn("Indexing assignment requires inferred type metadata", str(ctx.exception))

    def test_left_to_right_collection_evaluation_order(self):
        src = """
        fn f() -> int { return 1; }
        fn g() -> int { return 2; }
        record Pair { a: int; b: int; }
        fn main() -> int {
            let xs: list[int] = [f(), g()];
            let p: Pair = Pair { a: f(), b: g() };
            return 0;
        }
        """
        ir = compile_text(src)
        code = ir["functions"]["main"]["code"]
        # List evaluation order
        list_idx = code.index(["MAKE_LIST", 2])
        self.assertEqual(code[list_idx - 2], ["CALL", "f", 0])
        self.assertEqual(code[list_idx - 1], ["CALL", "g", 0])
        # Record evaluation order
        rec_idx = code.index(["MAKE_RECORD", "Pair", ["a", "b"]])
        self.assertEqual(code[rec_idx - 2], ["CALL", "f", 0])
        self.assertEqual(code[rec_idx - 1], ["CALL", "g", 0])


class Stage0Milestone04Tests(unittest.TestCase):
    def run_source(self, source: str):
        output = []
        ir = compile_text(source)
        vm = VirtualMachine(ir, output=output.append)
        code = vm.run()
        return output, code, ir

    def test_list_construction_and_element_access(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [10, 20, 30];
            let ys: list[int] = [];
            print(xs[0]);
            print(xs[1]);
            print(xs[2]);
            print(len(ys));
            return 0;
        }
        """
        out, code, _ = self.run_source(src)
        self.assertEqual(out, ["10", "20", "30", "0"])

    def test_list_set_mutation(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [1, 2, 3];
            xs[0] = 100;
            xs[2] = 300;
            print(xs[0]);
            print(xs[1]);
            print(xs[2]);
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["100", "2", "300"])

    def test_list_bounds_and_negative_index_errors(self):
        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source("fn main() -> int { let xs: list[int] = [1]; let x = xs[5]; return 0; }")
        self.assertIn("Indeks list di luar batas", str(ctx.exception))

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source("fn main() -> int { let xs: list[int] = [1]; let i: int = 0 - 1; let x = xs[i]; return 0; }")
        self.assertIn("Indeks list di luar batas", str(ctx.exception))

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source("fn main() -> int { let xs: list[int] = [1]; xs[2] = 10; return 0; }")
        self.assertIn("Indeks list di luar batas", str(ctx.exception))

    def test_map_construction_and_access(self):
        src = """
        fn main() -> int {
            let m: map[string, int] = {"alpha": 1, "beta": 2};
            let empty: map[string, int] = {};
            print(m["alpha"]);
            print(m["beta"]);
            print(len(empty));
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["1", "2", "0"])

    def test_map_set_insert_and_overwrite(self):
        src = """
        fn main() -> int {
            let m: map[string, int] = {"k": 1};
            m["k"] = 42;
            m["new_key"] = 99;
            print(m["k"]);
            print(m["new_key"]);
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["42", "99"])

    def test_map_missing_key_raises_runtime_error(self):
        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { let m: map[string, int] = {"a": 1}; let x = m["b"]; return 0; }')
        self.assertIn("Key map tidak ditemukan", str(ctx.exception))

    def test_record_instantiation_field_get_and_set(self):
        src = """
        record Person { name: string; age: int; }
        fn main() -> int {
            let p: Person = Person { name: "Alice", age: 30 };
            print(p.name);
            print(p.age);
            p.age = 31;
            print(p.age);
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["Alice", "30", "31"])

    def test_string_unicode_indexing(self):
        src = """
        fn main() -> int {
            let s: string = "RANCAGE";
            print(s[0]);
            print(s[6]);
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["R", "E"])

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { let s: string = "abc"; let i: int = 0 - 1; let c = s[i]; return 0; }')
        self.assertIn("Indeks string di luar batas", str(ctx.exception))

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { let s: string = "abc"; let c = s[10]; return 0; }')
        self.assertIn("Indeks string di luar batas", str(ctx.exception))

    def test_null_dereference_error(self):
        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source("""
            record Node { val: int; }
            fn main() -> int {
                let n: Node? = null;
                print(n.val);
                return 0;
            }
            """)
        self.assertIn("Null reference dereference", str(ctx.exception))

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source("""
            record Node { val: int; }
            fn main() -> int {
                let n: Node? = null;
                n.val = 10;
                return 0;
            }
            """)
        self.assertIn("Null reference dereference", str(ctx.exception))

    def test_intrinsics_len_on_various_types(self):
        src = """
        fn main() -> int {
            let s: string = "hello";
            let xs: list[int] = [1, 2, 3];
            let m: map[string, int] = {"a": 1, "b": 2, "c": 3, "d": 4};
            print(len(s));
            print(len(xs));
            print(len(m));
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["5", "3", "4"])

    def test_intrinsics_push_and_pop(self):
        src = """
        fn main() -> int {
            let xs: list[int] = [10];
            push(xs, 20);
            push(xs, 30);
            print(len(xs));
            let popped: int = pop(xs);
            print(popped);
            print(len(xs));
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["3", "30", "2"])

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source("fn main() -> int { let xs: list[int] = []; pop(xs); return 0; }")
        self.assertIn("Operasi pop pada list kosong", str(ctx.exception))

    def test_intrinsics_ord_and_chr(self):
        src = """
        fn main() -> int {
            let code: int = ord("A");
            let ch: string = chr(66);
            print(code);
            print(ch);
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["65", "B"])

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { ord("AB"); return 0; }')
        self.assertIn("Fungsi ord membutuhkan string tepat 1 karakter", str(ctx.exception))

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { chr(0 - 1); return 0; }')
        self.assertIn("Code point Unicode tidak valid", str(ctx.exception))

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { chr(55296); return 0; }')
        self.assertIn("Code point Unicode tidak valid", str(ctx.exception))

    def test_intrinsics_slice(self):
        src = """
        fn main() -> int {
            let s: string = "RANCAGE";
            let sub: string = slice(s, 1, 3);
            let clamped: string = slice(s, 4, 100);
            print(sub);
            print(clamped);
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["ANC", "AGE"])

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { slice("abc", 0 - 1, 1); return 0; }')
        self.assertIn("Argumen slice di luar batas", str(ctx.exception))

        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source('fn main() -> int { slice("abc", 5, 1); return 0; }')
        self.assertIn("Argumen slice di luar batas", str(ctx.exception))

    def test_intrinsics_map_has_and_remove(self):
        src = """
        fn main() -> int {
            let m: map[string, int] = {"key": 42};
            print(map_has(m, "key"));
            print(map_has(m, "other"));
            let removed: bool = map_remove(m, "key");
            print(removed);
            print(map_has(m, "key"));
            let not_found_rem: bool = map_remove(m, "key");
            print(not_found_rem);
            return 0;
        }
        """
        out, _, _ = self.run_source(src)
        self.assertEqual(out, ["true", "false", "true", "false", "false"])

    def test_defensive_bytecode_validation_rejections(self):
        bad_ir = {"format": "RANCAGE-IR", "version": "0.2", "entry": "main",
                  "functions": {"main": {"params": [], "code": [["INVALID_OPCODE"]]}}}
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_ir)
        self.assertIn("Instruksi tidak dikenal", str(ctx.exception))

        bad_rec = {"format": "RANCAGE-IR", "version": "0.2", "entry": "main",
                   "records": {},
                   "functions": {"main": {"params": [], "code": [["MAKE_RECORD", "Point", ["x", "y"]]]}}}
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_rec)
        self.assertIn("tidak ditemukan pada metadata records", str(ctx.exception))

        bad_fields = {"format": "RANCAGE-IR", "version": "0.2", "entry": "main",
                      "records": {"Point": {"fields": [{"name": "x", "type": "int"}]}},
                      "functions": {"main": {"params": [], "code": [["MAKE_RECORD", "Point", ["x", "y"]]]}}}
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_fields)
        self.assertIn("tidak cocok dengan deklarasi record", str(ctx.exception))

        bad_call = {"format": "RANCAGE-IR", "version": "0.2", "entry": "main",
                    "functions": {"main": {"params": [], "code": [["CALL", "len", 2]]}}}
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_call)
        self.assertIn("Arity pemanggilan intrinsic", str(ctx.exception))

        bad_list_op = {"format": "RANCAGE-IR", "version": "0.2", "entry": "main",
                       "functions": {"main": {"params": [], "code": [["MAKE_LIST"]]}}}
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_list_op)
        self.assertIn("Operand MAKE_LIST tidak valid", str(ctx.exception))

    def test_resource_limits_enforcement(self):
        ir = compile_text('fn main() -> int { while (true) { } return 0; }')
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(ir, max_steps=50).run()
        self.assertIn("Batas instruksi program terlampaui", str(ctx.exception))

        rec_src = 'fn recurse(n: int) -> int { return recurse(n + 1); } fn main() -> int { return recurse(0); }'
        ir_rec = compile_text(rec_src)
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(ir_rec, max_depth=10).run()
        self.assertIn("Batas kedalaman pemanggilan fungsi terlampaui", str(ctx.exception))

    def test_end_to_end_composite_program(self):
        src = """
        record Token {
            kind: int;
            text: string;
        }
        fn main() -> int {
            let tokens: list[Token] = [];
            push(tokens, Token { kind: 1, text: "let" });
            push(tokens, Token { kind: 2, text: "x" });
            push(tokens, Token { kind: 3, text: "=" });
            push(tokens, Token { kind: 4, text: "10" });

            let count: int = len(tokens);
            print(count);

            let syms: map[string, int] = {};
            syms[tokens[1].text] = 10;
            print(syms["x"]);

            let s: string = "RANCAGE-v0.2";
            let prefix: string = slice(s, 0, 7);
            print(prefix);
            print(tokens[0].text);
            return count;
        }
        """
        out, code, _ = self.run_source(src)
        self.assertEqual(out, ["4", "10", "RANCAGE", "let"])
        self.assertEqual(code, 4)

    def test_record_out_of_order_field_initialization(self):
        src = """
        record Config {
            timeout: int;
            retries: int;
            name: string;
        }
        fn main() -> int {
            let c: Config = Config { name: "test", timeout: 500, retries: 3 };
            print(c.name);
            print(c.timeout);
            print(c.retries);
            return 0;
        }
        """
        out, code, _ = self.run_source(src)
        self.assertEqual(out, ["test", "500", "3"])
        self.assertEqual(code, 0)

        bad_ir = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "records": {
                "Point": {"fields": [{"name": "x", "type": "int"}, {"name": "y", "type": "int"}]}
            },
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 1],
                        ["PUSH", 2],
                        ["MAKE_RECORD", "Point", ["x", "x"]],
                        ["POP"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_ir)
        self.assertIn("Field operand MAKE_RECORD tidak cocok", str(ctx.exception))

    def test_record_cycle_safe_printing(self):
        node = RecordInstance("Node", {"val": 1})
        node.fields["self_ref"] = node
        s = repr(node)
        self.assertIn("<cycle>", s)
        self.assertIn("Node", s)

        lst = [10]
        lst.append(lst)
        s_lst = format_value(lst)
        self.assertIn("<cycle>", s_lst)

        curr = RecordInstance("Chain", {"val": 0})
        root = curr
        for i in range(40):
            nxt = RecordInstance("Chain", {"val": i + 1})
            curr.fields["next"] = nxt
            curr = nxt
        formatted = repr(root)
        self.assertIn("{...}", formatted)

    def test_integer_64bit_overflow_checks(self):
        src_add = f"""
        fn main() -> int {{
            let a: int = {MAX_INT64};
            let b: int = a + 1;
            return b;
        }}
        """
        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source(src_add)
        self.assertIn("Integer overflow pada operasi penjumlahan", str(ctx.exception))

        src_sub = """
        fn main() -> int {
            let a: int = -9223372036854775807 - 1;
            let b: int = a - 1;
            return b;
        }
        """
        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source(src_sub)
        self.assertIn("Integer overflow pada operasi pengurangan", str(ctx.exception))

        src_mul = f"""
        fn main() -> int {{
            let a: int = {MAX_INT64};
            let b: int = a * 2;
            return b;
        }}
        """
        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source(src_mul)
        self.assertIn("Integer overflow pada operasi perkalian", str(ctx.exception))

        src_neg = """
        fn main() -> int {
            let a: int = -9223372036854775807 - 1;
            let b: int = -a;
            return b;
        }
        """
        with self.assertRaises(RancageRuntimeError) as ctx:
            self.run_source(src_neg)
        self.assertIn("Integer overflow pada operasi negasi", str(ctx.exception))

        bad_ir = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", MAX_INT64 + 1],
                        ["RETURN"],
                    ],
                }
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_ir)
        self.assertIn("Konstanta integer di luar batas 64-bit", str(ctx.exception))

    def test_pre_execution_user_function_call_arity_validation(self):
        bad_ir = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "add": {
                    "params": ["x", "y"],
                    "code": [
                        ["LOAD", "x"],
                        ["LOAD", "y"],
                        ["ADD"],
                        ["RETURN"],
                    ],
                },
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 42],
                        ["CALL", "add", 1],
                        ["RETURN"],
                    ],
                },
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_ir)
        self.assertIn("Arity pemanggilan fungsi 'add' tidak valid: diharapkan 2, menerima 1", str(ctx.exception))

    def test_cumulative_allocation_budget_enforcement(self):
        src = """
        fn main() -> int {
            let items: list[int] = [];
            let i: int = 0;
            while (i < 100) {
                push(items, i);
                i = i + 1;
            }
            return len(items);
        }
        """
        ir = compile_text(src)
        vm = VirtualMachine(ir)
        self.assertEqual(vm.run(), 100)

        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(ir, max_allocated_units=20).run()
        self.assertIn("Batas alokasi memori program terlampaui", str(ctx.exception))

        src_str = """
        fn main() -> int {
            let s: string = "a";
            let i: int = 0;
            while (i < 50) {
                s = s + "bb";
                i = i + 1;
            }
            return len(s);
        }
        """
        ir_str = compile_text(src_str)
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(ir_str, max_allocated_units=30).run()
        self.assertIn("Batas alokasi memori program terlampaui", str(ctx.exception))


class Stage0Milestone04QAVerificationTests(unittest.TestCase):
    def run_source(self, source: str):
        ir = compile_text(source)
        output = []
        vm = VirtualMachine(ir, output=lambda val: output.append(str(val)))
        code = vm.run()
        return output, code, vm

    def test_qa_finding1_record_field_permutations_and_eval_order(self):
        src = """
        record ComplexRecord {
            d: int;
            c: int;
            b: int;
            a: int;
        }
        fn main() -> int {
            let r: ComplexRecord = ComplexRecord { a: 10, b: 20, c: 30, d: 40 };
            print(r.a);
            print(r.b);
            print(r.c);
            print(r.d);
            return 0;
        }
        """
        out, code, _ = self.run_source(src)
        self.assertEqual(out, ["10", "20", "30", "40"])
        self.assertEqual(code, 0)

        ir = compile_text("""
        record Pair {
            first: int;
            second: int;
        }
        fn main() -> int {
            let p: Pair = Pair { second: 200, first: 100 };
            return p.first + p.second;
        }
        """)
        vm = VirtualMachine(ir)
        self.assertEqual(vm.run(), 300)

        bad_ir_missing = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "records": {
                "R": {"fields": [{"name": "x", "type": "int"}, {"name": "y", "type": "int"}]}
            },
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 1],
                        ["MAKE_RECORD", "R", ["x"]],
                        ["RETURN"],
                    ],
                }
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_ir_missing)
        self.assertIn("Field operand MAKE_RECORD tidak cocok", str(ctx.exception))

        bad_ir_unknown = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "records": {
                "R": {"fields": [{"name": "x", "type": "int"}]}
            },
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 1],
                        ["MAKE_RECORD", "R", ["z"]],
                        ["RETURN"],
                    ],
                }
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(bad_ir_unknown)
        self.assertIn("Field operand MAKE_RECORD tidak cocok", str(ctx.exception))

    def test_qa_finding2_cycle_safety_dag_and_depth_limits(self):
        leaf = RecordInstance("Leaf", {"data": 999})
        parent_a = RecordInstance("ParentA", {"leaf": leaf})
        parent_b = RecordInstance("ParentB", {"leaf": leaf})
        root = [parent_a, parent_b]
        formatted = format_value(root)
        self.assertNotIn("<cycle>", formatted)
        self.assertEqual(formatted.count("999"), 2)

        node_a = RecordInstance("NodeA", {"val": "A"})
        node_b = RecordInstance("NodeB", {"val": "B"})
        node_a.fields["peer"] = node_b
        node_b.fields["peer"] = node_a
        repr_a = repr(node_a)
        self.assertIn("<cycle>", repr_a)
        self.assertIn("NodeA", repr_a)
        self.assertIn("NodeB", repr_a)

        m = {"tag": "root"}
        m["self"] = m
        repr_m = format_value(m)
        self.assertIn("<cycle>", repr_m)

        nested_list = [0]
        for _ in range(35):
            nested_list = [nested_list]
        self.assertIn("[...]", format_value(nested_list))

        nested_map = {"k": 0}
        for _ in range(35):
            nested_map = {"k": nested_map}
        self.assertIn("{...}", format_value(nested_map))

    def test_qa_finding3_signed_64bit_bounds_and_operations(self):
        ir_min = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", MIN_INT64],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_min)
        self.assertEqual(vm.run(), MIN_INT64)

        ir_max = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", MAX_INT64],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_max)
        self.assertEqual(vm.run(), MAX_INT64)

        ir_under = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", MIN_INT64 - 1],
                        ["RETURN"],
                    ],
                }
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(ir_under)
        self.assertIn("Konstanta integer di luar batas 64-bit", str(ctx.exception))

        ir_float = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 1e20],
                        ["PUSH", 2e20],
                        ["ADD"],
                        ["POP"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm_float = VirtualMachine(ir_float)
        self.assertEqual(vm_float.run(), 0)

    def test_qa_finding4_pre_execution_call_arity_in_dead_code(self):
        dead_call_user_fn = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "target": {
                    "params": ["a", "b"],
                    "code": [["PUSH", 0], ["RETURN"]],
                },
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 0],
                        ["RETURN"],
                        ["PUSH", 1],
                        ["CALL", "target", 1],
                        ["RETURN"],
                    ],
                }
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(dead_call_user_fn)
        self.assertIn("Arity pemanggilan fungsi 'target' tidak valid", str(ctx.exception))

        dead_call_intrinsic = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 0],
                        ["RETURN"],
                        ["PUSH", 1],
                        ["CALL", "len", 2],
                        ["RETURN"],
                    ],
                }
            },
        }
        with self.assertRaises(RancageRuntimeError) as ctx:
            VirtualMachine(dead_call_intrinsic)
        self.assertIn("Arity pemanggilan intrinsic 'len' tidak valid", str(ctx.exception))

    def test_qa_finding5_allocation_accounting_granularity(self):
        ir_list = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 1],
                        ["PUSH", 2],
                        ["PUSH", 3],
                        ["MAKE_LIST", 3],
                        ["POP"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_list)
        vm.run()
        self.assertEqual(vm.allocated_units, 4)

        ir_map = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", "k1"],
                        ["PUSH", 1],
                        ["PUSH", "k2"],
                        ["PUSH", 2],
                        ["MAKE_MAP", 2],
                        ["POP"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_map)
        vm.run()
        self.assertEqual(vm.allocated_units, 3)

        ir_map_set = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", "k"],
                        ["PUSH", 10],
                        ["MAKE_MAP", 1],
                        ["STORE", "m"],
                        ["LOAD", "m"],
                        ["PUSH", "k"],
                        ["PUSH", 99],
                        ["MAP_SET"],
                        ["LOAD", "m"],
                        ["PUSH", "new_k"],
                        ["PUSH", 100],
                        ["MAP_SET"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_map_set)
        vm.run()
        self.assertEqual(vm.allocated_units, 3)

        ir_chr = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 65],
                        ["CALL", "chr", 1],
                        ["POP"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_chr)
        vm.run()
        self.assertEqual(vm.allocated_units, 1)

        ir_sget = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", "hello"],
                        ["PUSH", 0],
                        ["STRING_GET"],
                        ["POP"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_sget)
        vm.run()
        self.assertEqual(vm.allocated_units, 1)

        ir_slice = {
            "format": "RANCAGE-IR",
            "version": "0.2",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", "abcdef"],
                        ["PUSH", 1],
                        ["PUSH", 3],
                        ["CALL", "slice", 3],
                        ["POP"],
                        ["PUSH", 0],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir_slice)
        vm.run()
        self.assertEqual(vm.allocated_units, 3)

        with self.assertRaises(RancageRuntimeError) as ctx:
            vm._charge_allocation(-10)
        self.assertIn("Unit alokasi tidak valid", str(ctx.exception))

    def test_qa_adversarial_null_dereferences_and_bounds(self):
        ir_null_cases = [
            ("GET_FIELD", [["PUSH", None], ["GET_FIELD", "x"]]),
            ("SET_FIELD", [["PUSH", None], ["PUSH", 1], ["SET_FIELD", "x"]]),
            ("LIST_GET", [["PUSH", None], ["PUSH", 0], ["LIST_GET"]]),
            ("LIST_SET", [["PUSH", None], ["PUSH", 0], ["PUSH", 1], ["LIST_SET"]]),
            ("MAP_GET", [["PUSH", None], ["PUSH", "k"], ["MAP_GET"]]),
            ("MAP_SET", [["PUSH", None], ["PUSH", "k"], ["PUSH", 1], ["MAP_SET"]]),
            ("STRING_GET", [["PUSH", None], ["PUSH", 0], ["STRING_GET"]]),
        ]
        for name, code in ir_null_cases:
            ir = {
                "format": "RANCAGE-IR",
                "version": "0.2",
                "entry": "main",
                "functions": {"main": {"params": [], "code": code + [["RETURN"]]}},
            }
            with self.assertRaises(RancageRuntimeError) as ctx:
                VirtualMachine(ir).run()
            self.assertIn("Null reference dereference", str(ctx.exception), f"Failed for {name}")


class Stage0Milestone05IntegrationTests(unittest.TestCase):
    def test_rancage_ir_0_1_backward_compatibility(self):
        ir = {
            "format": "RANCAGE-IR",
            "version": "0.1",
            "entry": "main",
            "functions": {
                "main": {
                    "params": [],
                    "code": [
                        ["PUSH", 40],
                        ["PUSH", 2],
                        ["ADD"],
                        ["RETURN"],
                    ],
                }
            },
        }
        vm = VirtualMachine(ir)
        self.assertEqual(vm.run(), 42)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "v01.rcb"
            path.write_text(json.dumps(ir), encoding="utf-8")
            loaded_vm = VirtualMachine.from_file(path)
            self.assertEqual(loaded_vm.run(), 42)
            self.assertEqual(cli_main(["run", str(path)]), 42)

    def test_golden_path_stage0_integration(self):
        source = """
record Node {
    val: int;
    next: Node?;
}

fn process_string(s: string) -> string {
    let sub: string = slice(s, 0, 4);
    let code: int = ord(slice(sub, 0, 1));
    let ch: string = chr(code);
    return sub + ch;
}

fn main() -> int {
    let head: Node = Node { val: 10, next: null };
    let second: Node = Node { val: 20, next: head };
    let tail: Node = Node { val: 30, next: second };

    let total: int = 0;
    let curr: Node? = tail;
    while (curr != null) {
        total = total + curr.val;
        curr = curr.next;
    }

    let nums: list[int] = [1, 2, 3];
    push(nums, 4);
    let p: int = pop(nums);
    total = total + p + len(nums);

    let lookup: map[string, int] = {"alpha": 100, "beta": 200};
    lookup["gamma"] = 300;
    if (map_has(lookup, "beta")) {
        total = total + lookup["beta"];
        let removed: bool = map_remove(lookup, "beta");
        if (removed && !map_has(lookup, "beta")) {
            total = total + 5;
        }
    }

    let s: string = process_string("rancage");
    if (len(s) == 5) {
        total = total + len(s);
    }

    print(tail);
    return total;
}
"""
        program = parse_source(source)
        check_types(program)
        ir = compile_program(program)

        out = []
        vm = VirtualMachine(ir, output=out.append)
        ret = vm.run()

        self.assertEqual(ret, 277)
        self.assertGreater(vm.allocated_units, 0)
        self.assertEqual(len(out), 1)
        self.assertIn("Node", out[0])
        self.assertIn("'val': 30", out[0])
        self.assertIn("'val': 20", out[0])
        self.assertIn("'val': 10", out[0])

    def test_cli_stage0_workflow_check_build_run(self):
        source = """
record Point {
    x: int;
    y: int;
}

fn main() -> int {
    let pt: Point = Point { x: 5, y: 7 };
    print(pt);
    return pt.x + pt.y;
}
"""
        with tempfile.TemporaryDirectory() as temp:
            src_path = Path(temp) / "test_prog.cage"
            rcb_path = Path(temp) / "test_prog.rcb"
            src_path.write_text(source, encoding="utf-8")

            # 1. Test check command
            check_stdout = io.StringIO()
            with contextlib.redirect_stdout(check_stdout):
                code = cli_main(["check", str(src_path)])
            self.assertEqual(code, 0)
            self.assertIn(f"valid (RANCAGE {__version__})", check_stdout.getvalue())

            # 2. Test build command
            build_stdout = io.StringIO()
            with contextlib.redirect_stdout(build_stdout):
                code = cli_main(["build", str(src_path), "-o", str(rcb_path)])
            self.assertEqual(code, 0)
            self.assertTrue(rcb_path.exists())

            # 3. Test run command on .rcb
            run_rcb_stdout = io.StringIO()
            with contextlib.redirect_stdout(run_rcb_stdout):
                code = cli_main(["run", str(rcb_path)])
            self.assertEqual(code, 12)
            self.assertIn("Point {'x': 5, 'y': 7}", run_rcb_stdout.getvalue())

            # 4. Test run command on .cage directly
            run_cage_stdout = io.StringIO()
            with contextlib.redirect_stdout(run_cage_stdout):
                code = cli_main(["run", str(src_path)])
            self.assertEqual(code, 12)
            self.assertIn("Point {'x': 5, 'y': 7}", run_cage_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
