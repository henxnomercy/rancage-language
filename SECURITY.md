# RANCAGE Security Policy

## Scope and support status

RANCAGE is pre-1.0. The current VM is a small reference runtime, not a hardened
sandbox for hostile or multi-tenant workloads. The Windows standalone package
bundles the Python runtime; packaging is not a security boundary.

Security fixes are considered for the current `0.2.0-alpha.1` development
preview. The frozen `v0.1.0` tag is not promised ongoing security maintenance.

## Implemented defenses

- Static type checking during source compilation.
- JSON-only bytecode loading (no pickle or arbitrary-code deserialization).
- Opcode allowlist validation.
- Execution-step and call-depth limits.
- No language opcodes for filesystem, network, process creation, dynamic
  imports, or native calls.

These safeguards do not make the VM safe for untrusted workloads. Do not run
untrusted RANCAGE programs in a process that has access to sensitive resources
and assume the VM is an OS security boundary. Use OS/container isolation.

## Known limitations

- No cryptographic signing or encryption of `.rcb` files.
- No obfuscation or anti-tamper protection.
- No OS-level sandboxing, memory isolation, or formal verification.
- No secure secret storage.
- PyInstaller bundles can be inspected and unpacked.

Do not put API keys, passwords, access tokens, signing keys, or other secrets
inside RANCAGE source files or distributed bytecode.

## Reporting a vulnerability

The maintainer will enable GitHub **private vulnerability reporting** after
this repository is made public. GitHub currently offers this feature to owners
and administrators of public repositories. Once enabled, use the repository's
**Security / Advisories → Report a vulnerability** flow. Do not publish exploit
details, proof-of-concept code, or sensitive reproduction steps in a public
issue or discussion.

Until the private reporting form is visible, contact the maintainer through
the GitHub profile to request a private reporting channel; do not include
sensitive vulnerability details in a public message. No response-time SLA is
currently promised.
