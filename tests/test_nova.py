import json
import tempfile
import unittest
from pathlib import Path

from nova.compiler import compile_program
from nova.lexer import NovaSyntaxError
from nova.parser import parse_source
from nova.typesys import NovaTypeError, check_types
from nova.vm import NovaRuntimeError, VirtualMachine


def compile_text(source):
    program = parse_source(source)
    check_types(program)
    return compile_program(program)


class NovaLanguageTests(unittest.TestCase):
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
        with self.assertRaises(NovaTypeError):
            compile_text('fn main() -> int { let x: int = "wrong"; return 0; }')

    def test_const_cannot_be_assigned(self):
        with self.assertRaises(NovaTypeError):
            compile_text('fn main() -> int { const x: int = 1; x = 2; return 0; }')

    def test_division_by_zero(self):
        ir = compile_text('fn main() -> int { let x: float = 1.0 / 0.0; print(x); return 0; }')
        with self.assertRaises(NovaRuntimeError):
            VirtualMachine(ir, output=lambda _: None).run()

    def test_bytecode_roundtrip(self):
        ir = compile_text('fn main() -> int { print("roundtrip"); return 0; }')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "program.nvm"
            path.write_text(json.dumps(ir), encoding="utf-8")
            out = []
            vm = VirtualMachine.from_file(path, output=out.append)
            self.assertEqual(vm.run(), 0)
            self.assertEqual(out, ["roundtrip"])

    def test_nonvoid_must_return(self):
        with self.assertRaises(NovaTypeError):
            compile_text('fn main() -> int { let x: int = 2; }')

    def test_nested_variable_shadowing_is_rejected(self):
        source = '''fn main() -> int {
            let x: int = 1;
            if (true) { let x: int = 2; }
            print(x);
            return 0;
        }'''
        with self.assertRaises(NovaTypeError):
            compile_text(source)

    def test_execution_budget(self):
        ir = compile_text('fn main() -> int { while (true) { print(1); } return 0; }')
        with self.assertRaises(NovaRuntimeError):
            VirtualMachine(ir, output=lambda _: None, max_steps=20).run()

    def test_mixed_numeric_equality(self):
        out, _, _ = self.run_source('fn main() -> int { print(1 == 1.0); return 0; }')
        self.assertEqual(out, ["true"])

    def test_invalid_opcode_is_rejected(self):
        bad = {"format": "NOVA-IR", "version": "0.1", "entry": "main",
               "functions": {"main": {"params": [], "code": [["HOST_EXEC", "print(1)"]]}}}
        with self.assertRaises(NovaRuntimeError):
            VirtualMachine(bad)

    def test_unknown_character(self):
        with self.assertRaises(NovaSyntaxError):
            parse_source('fn main() -> int { @ return 0; }')


if __name__ == "__main__":
    unittest.main()
