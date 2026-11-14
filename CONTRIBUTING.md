# Contributing to RANCAGE

RANCAGE is an experimental pre-1.0 programming-language project. The `v0.1.0`
language baseline is frozen; the `0.2.0-alpha.1` preview focuses on Windows
standalone packaging and publication hygiene.

## Before changing code

- Read `AGENTS.md`, `PROJECT_STATUS.md`, `SPEC.md`, `SECURITY.md`, and `LICENSE`.
- Open an issue or create a clearly scoped task.
- Work on a feature branch; do not commit directly to `main` for code changes.
- Do not submit code copied from third-party projects unless its license and
  provenance are compatible and recorded.
- Until a contributor agreement or contribution terms are published, discuss
  substantive external code contributions with the maintainer before opening
  a pull request. A pull request alone must not be treated as a transfer of
  copyright ownership.

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
PYTHONPATH=src python -m rancage --version
PYTHONPATH=src python -m rancage check examples/hello.cage
PYTHONPATH=src python -m rancage run examples/hello.cage
```

All tests must pass. Do not delete or weaken tests to make a change appear
valid. Changes to compiler, parser, type checker, VM, or bytecode format require
focused regression tests and an update to `SPEC.md` when language behavior
changes.

## Licensing boundary

- RANCAGE compiler/runtime core is proprietary.
- Only SDK materials explicitly designated as MIT-licensed are covered by
  `licenses/SDK-MIT.txt`.
- Tests, examples, documentation, build scripts, and other repository files
  are not automatically MIT-licensed. Follow the notice attached to each file
  and ask the maintainer before reusing them.
- Do not assume the project accepts contributions under an assignment or
  license grant that has not been stated in a published contributor agreement.

## Scope discipline

New syntax, language features, IR revisions, and platform backends belong in a
later development branch/version after explicit approval from the project
owner. A planned target is not a supported target; it must pass its own
build and conformance tests before it is advertised as supported.
