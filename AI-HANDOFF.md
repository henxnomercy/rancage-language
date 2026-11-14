# AI Handoff — RANCAGE 0.2.0-alpha.1

## Source of truth

- Published baseline: `v0.1.0`, commit `556b37f` (immutable).
- Current development line: `0.2.0-alpha.1`.
- Active compiler implementation: Python 3.10+.
- Canonical compiler: `src/rancage/`.
- Language specification: `SPEC.md`.
- Implementation policy: `IMPLEMENTATION_DECISION.md`.

## Current task

Create a Windows standalone packaging preview using PyInstaller. This is a distribution convenience: the executable bundles Python; it is not native compilation and not self-hosting.

## Added files

- `cage_entry.py`: package entry point.
- `requirements-build.txt`: pinned build-only PyInstaller dependency.
- `build-windows.ps1`: builds one-file and one-folder Windows executables and distribution ZIP.
- `test-bundle.ps1`: smoke-tests both executable variants, including `.rcb` build/run.
- `.github/workflows/standalone-windows.yml`: Windows CI build and artifact upload.
- `BUILDING-STANDALONE.md` and `THIRD-PARTY-NOTICES.md`: build and distribution documentation.

## Verification requirements

- Re-run all 13 source tests.
- On Windows, install `requirements-build.txt`, run `build-windows.ps1`, and run `test-bundle.ps1`.
- GitHub Actions must be green before calling the Windows executable verified.
- Download and test the artifact on a clean Windows machine without Python to verify the end-user requirement.

## Next smallest task

Push this preview to the RANCAGE repository, inspect the `RANCAGE Windows Standalone Build` workflow, download its artifact, and test `cage.exe` on a Windows environment without Python installed.
