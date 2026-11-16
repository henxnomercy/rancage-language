# RANCAGE Project Status

**Frozen language baseline:** `v0.1.0` (historical NOVA baseline)
**Current development preview:** `0.2.0-alpha.1`
**Active implementation language:** Python 3.10+
**Current focus:** RANCAGE/CAGE identity migration, Windows standalone preview,
and publication preparation under a hybrid licensing model.

## Version policy

Do not modify the published `v0.1.0` tag. It is retained as the historical
NOVA baseline. Packaging and identity migration are later commits in the
unreleased `0.2.0-alpha.1` development preview. The language grammar and
semantics remain at the v0.1 baseline unless a separately reviewed change is
approved.

## Implemented

- Lexer, parser, AST, and static type checker.
- JSON RANCAGE-IR compiler and bounded reference VM.
- CLI commands `check`, `build`, `run`, and `targets`.
- Functions, variables, conditions, loops, and execution limits.
- Canonical `.cage` source and `.rcb` bytecode extensions.
- `cage` / `cage.exe` CLI, with `rancage` as an alias.
- 74 unit, integration, and QA verification tests covering language features, Stage 0 milestones M0.1-M0.5, golden-path integration, RANCAGE-IR 0.1 compatibility, and post-audit runtime hardening.
- Windows one-file and one-folder PyInstaller packaging scripts and smoke tests.
- Stage 0 Milestone M0.5 implementation complete, pending QA verification and owner sign-off.

## Verification status

- The Windows standalone GitHub Actions workflow completed successfully for
the RANCAGE/CAGE migration preview and produced the Windows x64 artifact.
- The project maintainer manually tested the downloaded executable on Windows
without a separate Python installation: `--version`, source `check`/`run`,
bytecode `build`, and bytecode `run` succeeded for all three example programs.
- These checks validate the Windows x64 preview workflow and examples; they do
not establish native compilation, self-hosting, hardened isolation, or support
for other operating systems.

## Licensing status

The selected model is hybrid: RANCAGE compiler/runtime core is proprietary;
only files explicitly designated as SDK materials are under the MIT license.
The current `sdk/` directory contains a draft extension contract only. It is
not a stable external ABI or production SDK. The project-specific proprietary
terms are a maintainer-prepared draft and have not been reviewed by an
Indonesian intellectual-property lawyer. See `LICENSE` and the specific files
under `licenses/` for the intended scope.

The core license allows users to use an unmodified official CAGE release,
including commercially, to create and distribute their own RANCAGE programs
without royalties. It does not allow bundling or redistribution of RANCAGE Core
without separate permission.

## Publication checklist

- [x] Repository renamed to `rancage-language`.
- [x] RANCAGE/CAGE migration merged to `main`.
- [x] Hybrid licensing model selected and draft notices prepared locally.
- [x] Git history bundle reviewed for common secret patterns.
- [x] Review reachable commit author metadata; all commits use the GitHub
      noreply identity.
- [x] Remove the obsolete `nova.cmd` launcher; it has been deleted from the
      working tree and is pending inclusion in the migration commit.
- [x] Update package author metadata to `henxnomercy`.
- [x] Complete final review of publication and security guidance.
- [ ] Enable GitHub private vulnerability reporting immediately after the
      repository is made public.
- [ ] Complete final local diff review, commit, push, and CI checks.

## Not implemented

- Native machine-code code generation.
- Self-hosting compiler.
- Android, iOS, WebAssembly, Roblox/Luau, or other production backends.
- Code signing, updater, installer, hardened sandbox, bytecode encryption, or
  anti-tamper.
