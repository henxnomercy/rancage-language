# AI Handoff — NOVA v0.1.0

## Current source of truth

- Active baseline: NOVA 0.1.0.
- Active compiler implementation language: Python 3.10+.
- Canonical implementation: `src/nova/`.
- Language specification: `SPEC.md`.
- Implementation decision: `IMPLEMENTATION_DECISION.md`.
- Current status: `PROJECT_STATUS.md`.

## Important architecture decision

The project owner explicitly reverted the planned Rust implementation and selected Python because Python is already installed and reduces setup friction. The Rust Core experiment is superseded. Do not install Rust, add Cargo, or merge Rust Core into the canonical repository.

## Baseline verification

Recorded in the prepared package: 13 unit/integration tests passed in the available Linux environment. Windows wrapper and GitHub Actions results must be verified by the project owner after extraction and push.

## Current task

Stabilize and publish the Python v0.1.0 baseline. Do not add language features or platform backends to this frozen release.

## Handoff format for the next agent

When finishing a task, record:
1. Task and files changed.
2. Commands executed.
3. Exact test/build results (do not claim tests passed if not run).
4. Known limitations or failures.
5. Next smallest actionable task.
