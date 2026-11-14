# Instructions for RANCAGE coding agents

## Current source of truth

- Published baseline: `v0.1.0` (frozen).
- Current development preview: `0.2.0-alpha.1` (Windows standalone packaging).
- Active implementation language: Python 3.10+.
- Canonical implementation: `src/rancage/`.
- Language specification: `SPEC.md`.
- Implementation decision: `IMPLEMENTATION_DECISION.md`.
- Current project status: `PROJECT_STATUS.md`.

## Non-negotiable rules

1. Python is the approved implementation language for the active RANCAGE compiler, CLI, and reference VM. Do not add Rust/C/C++/Zig compiler code or Cargo files.
2. The earlier Rust Core experiment is superseded and must not be merged into the canonical repository.
3. Do not rewrite or move the published `v0.1.0` tag.
4. Do not change RANCAGE syntax, language semantics, CLI behavior, or RANCAGE-IR format in a packaging-only task.
5. PyInstaller is a build-time packaging dependency only. The packaged executable embeds Python; it is not a native compiler.
6. Do not claim a standalone target works until its build and smoke tests have passed on that target OS.
7. Never add API keys, tokens, passwords, signing keys, personal data, or `.env` files to Git.
8. Do not remove or weaken tests to make CI pass.
9. Preserve ownership notices in `licenses/` and third-party notices. Do not invent legal ownership.
10. Do not run destructive Git commands (`reset --hard`, `clean -fd`, force push, history rewrite) without explicit owner approval.

## Required workflow

1. Read `IMPLEMENTATION_DECISION.md`, `README.md`, `SPEC.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, and `SECURITY.md`.
2. Identify the smallest task and acceptance criteria.
3. Add or update tests.
4. Run `run-tests.cmd` on Windows or `PYTHONPATH=src python -m unittest discover -s tests -v` elsewhere.
5. For packaging tasks, install `requirements-build.txt`, run `build-windows.ps1`, then `test-bundle.ps1` on Windows.
6. Report exact commands and results. Do not claim unexecuted tests passed.
7. Update `AI-HANDOFF.md` with changes, results, limitations, and next task.

## Version policy

The published 0.1.0 tag is immutable. Current preview changes are unreleased development commits. Do not create a new stable release until source CI and target-platform executable smoke tests pass.
