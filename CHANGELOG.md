# Changelog

## 0.2.0-alpha.1 — Windows standalone packaging preview

- Established RANCAGE as the public language/project name, with `cage` / `cage.exe` as the short command and executable name.
- Changed source files to `.cage` and compiled bytecode files to `.rcb`; `.nova`, `.nvm`, and the interim `.rcg` source extension are no longer accepted by source CLI commands.
- Changed the emitted IR marker to `RANCAGE-IR`; the VM can still read legacy `NOVA-IR` payloads stored in `.rcb` files.
- Added a pinned, build-time-only PyInstaller dependency.
- Added Windows one-file and one-folder build scripts.
- Added bundled executable smoke tests covering CLI, source execution, bytecode build, and bytecode execution.
- Added a Windows GitHub Actions workflow that uploads standalone build artifacts.
- Added standalone build instructions and third-party notices.
- No intentional change to RANCAGE 0.1 language syntax, semantics, or RANCAGE-IR format.

## 0.1.0 — Initial release

- Initial lexer, parser, AST, static type checker, RANCAGE-IR compiler, reference VM, CLI, examples, and test suite.
