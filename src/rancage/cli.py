"""Command-line interface for RANCAGE 0.1."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .compiler import compile_program
from .lexer import RancageSyntaxError
from .parser import parse_source
from .typesys import RancageTypeError, check_types
from .vm import RancageRuntimeError, VirtualMachine
from .targets import TARGETS


def compile_source(path: Path) -> dict:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Tidak bisa membaca {path}: {exc}") from exc
    program = parse_source(source)
    check_types(program)
    return compile_program(program)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cage", description="RANCAGE Universal Language — Python reference compiler")
    parser.add_argument("--version", action="version", version=f"RANCAGE {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Periksa sintaks dan tipe source RANCAGE")
    check.add_argument("source", type=Path)
    build = sub.add_parser("build", help="Kompilasi source menjadi RANCAGE-IR bytecode (.rcb)")
    build.add_argument("source", type=Path)
    build.add_argument("-o", "--output", type=Path)
    run = sub.add_parser("run", help="Jalankan source .cage atau bytecode .rcb")
    run.add_argument("program", type=Path)
    run.add_argument("--max-steps", type=int, default=1_000_000)
    sub.add_parser("targets", help="Tampilkan target kompilasi dan status implementasinya")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check":
            if args.source.suffix.lower() != ".cage":
                print("Error: source harus berekstensi .cage", file=sys.stderr)
                return 2
            compile_source(args.source)
            print(f"OK: {args.source} valid (RANCAGE 0.1)")
            return 0
        if args.command == "build":
            if args.source.suffix.lower() != ".cage":
                print("Error: source harus berekstensi .cage", file=sys.stderr)
                return 2
            ir = compile_source(args.source)
            output = args.output or args.source.with_suffix(".rcb")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(ir, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Built: {output}")
            return 0
        if args.command == "targets":
            print("RANCAGE 0.1 target registry (planned != supported):")
            for target_id, name, status, notes in TARGETS:
                print(f"{target_id:12} {status:25} {name} — {notes}")
            return 0
        if args.command == "run":
            if args.max_steps < 1:
                print("Error: --max-steps harus lebih besar dari nol", file=sys.stderr)
                return 2
            if args.program.suffix.lower() == ".cage":
                ir = compile_source(args.program)
                vm = VirtualMachine(ir, max_steps=args.max_steps)
            elif args.program.suffix.lower() == ".rcb":
                vm = VirtualMachine.from_file(args.program, max_steps=args.max_steps)
            else:
                print("Error: input harus berekstensi .cage atau .rcb", file=sys.stderr)
                return 2
            return vm.run()
    except RancageSyntaxError as exc:
        print(f"{args.source if hasattr(args, 'source') else args.program}:{exc.line}:{exc.column}: SyntaxError: {exc.message}", file=sys.stderr)
        return 1
    except RancageTypeError as exc:
        print(f"{args.source if hasattr(args, 'source') else args.program}:{exc.span.line}:{exc.span.column}: TypeError: {exc.message}", file=sys.stderr)
        return 1
    except (RancageRuntimeError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
