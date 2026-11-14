# RANCAGE Security Policy

## Scope

RANCAGE is pre-1.0. The current VM is a small reference runtime, not a hardened sandbox for hostile multi-tenant workloads.

## Implemented in 0.1

- Static type checking during source compilation.
- JSON-only bytecode loading (no pickle or arbitrary code deserialization).
- Opcode allowlist validation.
- Execution-step and call-depth limits.
- No language opcodes for filesystem, network, process creation, dynamic imports, or native calls.

## Packaging note

The Windows standalone preview uses PyInstaller to bundle the Python runtime. This removes the separate Python installation requirement but does not encrypt, hide, or harden RANCAGE source/bytecode. Packaged applications can be inspected and unpacked.

## Not implemented

- Cryptographic signing or encryption of `.rcb` files.
- Obfuscation or control-flow flattening.
- Anti-debugging or anti-tamper.
- OS-level sandboxing, memory isolation, or formal verification.
- Secure secret storage.

Do not run untrusted RANCAGE programs in a process that has access to sensitive resources and assume the VM is a security boundary. Use OS/container isolation for untrusted workloads.

## Reporting

For a private report, contact the project maintainer after the project establishes an official security contact. Do not publish exploit details before a fix process exists. No official security response SLA has been established for this prototype.
