import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from rancage.compiler import compile_program
from rancage.cli import main as cli_main
from rancage.lexer import RancageSyntaxError
from rancage.parser import parse_source
from rancage.typesys import RancageTypeError, check_types
from rancage.vm import RancageRuntimeError, VirtualMachine


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


if __name__ == "__main__":
    unittest.main()
