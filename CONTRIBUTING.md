# Contributing to RANCAGE 0.1.0

RANCAGE 0.1.0 is frozen for its initial publication. During this freeze, changes should be limited to publication metadata, documentation corrections, build/release automation, and fixes required to restore the documented 0.1.0 behavior.

## Before changing code

- Read `AGENTS.md`, `PROJECT_STATUS.md`, `SPEC.md`, and `SECURITY.md`.
- Open an issue or create a clearly scoped task.
- Work on a feature branch; do not commit directly to `main` for code changes.

## Validation

On Windows:

```powershell
.\run-tests.cmd
.\cage.cmd check examples\hello.cage
.\cage.cmd run examples\hello.cage
```

On Linux/macOS:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m cage check examples/hello.cage
PYTHONPATH=src python -m cage run examples/hello.cage
```

All tests must pass. Do not delete or weaken tests to make a change appear valid.

## Scope discipline

New syntax, language features, IR revisions, and platform backends belong in a later development branch/version after explicit approval from the project owner.
