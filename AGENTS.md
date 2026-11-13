# Instructions for AI coding agents

## Project baseline

- Project: NOVA Universal Programming Language.
- Current baseline: `0.1.0`.
- Status: frozen for initial GitHub publication.
- Active implementation language: Python 3.10+.
- Read `IMPLEMENTATION_DECISION.md`, `README.md`, `SPEC.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, and `SECURITY.md` before making changes.

## Non-negotiable rules

1. Python is the approved implementation language for the active v0.1 compiler, CLI, and reference VM. Do not add Rust/C/C++/Zig compiler code or Cargo files to the canonical repository.
2. The earlier Rust Core archive is superseded and must not be merged into this repository.
3. Do not silently change NOVA syntax, language semantics, NOVA-IR format, CLI behavior, or package version in the 0.1.0 baseline.
4. Do not claim support for a platform/backend unless implementation and conformance tests exist. In 0.1.0, only the experimental Python reference VM is implemented.
5. Do not introduce third-party runtime dependencies without explaining why and updating `pyproject.toml` and documentation. Prefer the Python standard library for the current baseline.
6. Never add API keys, tokens, passwords, signing keys, personal data, or `.env` files to Git.
7. Do not remove or weaken tests just to make CI pass.
8. Preserve ownership notices in `licenses/`. Do not invent a copyright owner or legal license.
9. Do not run destructive Git commands (`reset --hard`, `clean -fd`, force push, history rewrite) without explicit project-owner approval.

## Required workflow

1. Identify the exact task and acceptance criteria before editing.
2. Make the smallest change that satisfies the task.
3. Add or update tests for behavior changes.
4. Run `run-tests.cmd` on Windows, or `PYTHONPATH=src python -m unittest discover -s tests -v` on Linux/macOS.
5. Verify the CLI using examples in `README.md`.
6. Summarize changed files, test results, known limitations, and follow-up in `AI-HANDOFF.md`.
7. Keep one implementation agent per task. Other agents may review but should not edit the same task simultaneously.

## Version policy

The 0.1.0 baseline is frozen. New language features belong to a later version or separately approved development branch. Publication preparation may add repository metadata, tests, CI, and documentation without changing 0.1 language semantics.
