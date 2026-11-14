# RANCAGE Founding Specification

**Document status:** adopted project baseline  
**Language version:** 0.1  
**Specification revision:** 2026-11-11  
**Working name:** RANCAGE (name is provisional and has not been trademark-cleared)

## 1. Mission

RANCAGE is intended to be a general-purpose, portable programming language with one source language and a hybrid compilation architecture. The project aims to support desktop, mobile, web, server, game-engine, embedded, industrial, and future computing environments through interchangeable backends and host integrations.

"Universal" is a design goal, not a claim that one executable can run unchanged on every device. Platform-specific APIs, SDKs, permissions, application packaging, CPU architectures, and runtime constraints still apply.

## 2. Adopted founding decisions

| Decision | Adopted value | Consequence |
|---|---|---|
| Compiler architecture | Hybrid | Platform-neutral RANCAGE IR plus native, VM, WebAssembly, and transpiler backends over time |
| Security ambition | Maximum | Defense in depth; security review and threat modelling are required for each release |
| Development priority | Universal by design | Stable language core and extensible target interface; implementation delivered incrementally |
| Ownership | Hybrid | Proposed proprietary compiler/runtime core with an open SDK and extension interface |

The hybrid ownership model is a project policy proposal. The final copyright owner, commercial terms, contributor agreement, and exact open-source license must be confirmed by the project owner before public distribution.

## 3. Language design

### 3.1 Source files

- Source extension: `.cage`
- Text encoding: UTF-8
- Case-sensitive identifiers
- Line comments: `// ...`
- Block comments: `/* ... */`
- Statements end with `;`
- Blocks use `{` and `}`

### 3.2 Primitive types

| Type | Meaning |
|---|---|
| `int` | Integer |
| `float` | Floating-point number |
| `bool` | `true` or `false` |
| `string` | UTF-8 text |
| `void` | No return value |

RANCAGE 0.1 uses static type checking. There is no implicit conversion between `int` and `float` in this release. The `+` operator also concatenates two strings.

### 3.3 Grammar sketch (0.1 subset)

```ebnf
program       = ["module" IDENT ";"] , function , { function } ;
function      = "fn" , IDENT , "(" , [parameters] , ")" , "->" , type , block ;
parameters    = parameter , { "," , parameter } ;
parameter     = IDENT , ":" , type ;
type          = "int" | "float" | "bool" | "string" | "void" ;
block         = "{" , { statement } , "}" ;
statement     = let | const | assignment | return | if | while | expression , ";" ;
let           = "let" , IDENT , [":" , type] , "=" , expression , ";" ;
const         = "const" , IDENT , [":" , type] , "=" , expression , ";" ;
assignment    = IDENT , "=" , expression , ";" ;
return        = "return" , [expression] , ";" ;
if            = "if" , "(" , expression , ")" , block , ["else" , block] ;
while         = "while" , "(" , expression , ")" , block ;
```

The executable parser in this repository is authoritative for the implemented 0.1 subset. The grammar sketch is explanatory, not a complete formal grammar.

### 3.4 Functions and entry point

- Functions are declared with `fn name(parameters) -> type { ... }`.
- All functions are module-level in 0.1.
- A program must define `fn main() -> int` or `fn main() -> void`.
- Non-void functions must statically return a value on every recognized path. A final `if/else` whose two branches return is recognized; loops are not assumed to execute.
- `print(value);` is the only built-in function in 0.1.
- Function-local names cannot be redeclared in nested blocks in 0.1.

### 3.5 Operators

Precedence, high to low:

1. Unary `!` and `-`
2. `*`, `/`, `%`
3. `+`, `-`
4. `<`, `<=`, `>`, `>=`
5. `==`, `!=`
6. `&&`
7. `||`

Boolean operators in 0.1 evaluate both operands; short-circuit semantics are reserved for a future language revision unless explicitly standardized earlier.

## 4. Compiler architecture

```text
.cage source
    -> Lexer
    -> Parser / AST
    -> Static type checker
    -> RANCAGE IR
    -> Selected backend
    -> target artifact + metadata
```

The RANCAGE IR is the stable semantic boundary between the language frontend and platform backends. Backends must document unsupported features and target-specific behavior. A backend must not silently change language semantics.

### 4.1 RANCAGE IR 0.1

The first implementation serializes a stack-based instruction representation as JSON with the header:

```json
{
  "format": "RANCAGE-IR",
  "version": "0.1",
  "module": "hello",
  "entry": "main",
  "functions": {}
}
```

The `.rcb` extension identifies this reference bytecode container. It is a development format, not yet a stable cross-version ABI or a hardened binary format.

### 4.2 Backend roadmap and status

| Backend / integration | Intended targets | Status in 0.1 |
|---|---|---|
| RANCAGE reference VM | Development, tests, portable bytecode execution | Implemented, experimental |
| Native | x86-64, ARM64, RISC-V; Windows, Linux, macOS | Planned |
| WebAssembly | Browser and WASI-style server environments | Planned |
| Managed | JVM and .NET environments | Planned |
| Transpiler | JavaScript, TypeScript, Lua/Luau, C, Kotlin, Swift | Planned |
| Embedded | ESP32, ARM MCUs, RISC-V MCUs | Planned |
| Engine adapters | Roblox, Unity, Unreal, Godot, other engines | Planned; each engine has its own integration constraints |

A platform appears in the roadmap only as an intended target. It is not supported until a backend/adapter exists and passes conformance tests on that platform.

## 5. Runtime and standard library policy

RANCAGE 0.1 includes only `print`. It intentionally has no filesystem, network, process, reflection, dynamic library loading, or native FFI operations. This keeps the initial VM small and limits accidental host access.

Future standard-library capabilities will be capability-oriented: an application receives only the host APIs and permissions it needs. Platform integrations must document permissions, data access, and failure modes.

## 6. Security model

### 6.1 Threat model

RANCAGE aims to reduce unauthorized modification, casual source recovery, and tampering. It does not promise that distributed client-side software is impossible to reverse engineer. A determined analyst controlling a device can inspect memory, observe behavior, patch binaries, or emulate execution.

### 6.2 Planned controls

- Secure build pipeline and reproducible-build checks where feasible.
- Bytecode/container validation and strict resource limits.
- Optional obfuscation and control-flow transformations, separately versioned and tested.
- Integrity checks and platform-specific anti-tamper signals, treated as deterrence rather than proof.
- Dependency pinning, SBOM, vulnerability reporting, and signed release artifacts.
- Secret management guidance: do not embed private keys, API secrets, or authoritative business logic in distributed client apps.
- Server-side execution for logic that must remain confidential or authoritative.

### 6.3 Implemented controls in 0.1

- No use of Python `eval`, `exec`, pickle, or dynamic imports in the VM.
- JSON bytecode header and instruction allowlist validation.
- Instruction budget and call-depth limit.
- No host filesystem, network, process, or native-call opcodes.
- Static type checks before compilation.

These controls are suitable for a learning/reference prototype, not a security certification. The JSON bytecode is inspectable and can be modified; no obfuscator, cryptographic protection, sandbox certification, or anti-tamper system is implemented in 0.1.

## 7. Compatibility and conformance

Each language release must include:

- Lexer and parser tests.
- Type-checking positive and negative tests.
- VM and backend conformance tests.
- Golden output tests for examples.
- Explicit feature/version declarations per backend.
- Backward-compatibility policy for the source language and IR.

## 8. Versioning

- `0.x`: pre-stable; syntax and IR may change.
- `1.0`: requires a published language specification, stable core semantics, conformance suite, backend support policy, and documented compatibility commitments.
- IR format versioning is independent from the language package version.

## 9. Current implementation boundary

This repository implements a real reference compiler pipeline and VM for the subset above. It does not yet generate `.exe`, APK/AAB, iOS applications, WebAssembly, native machine code, Roblox scripts, or engine projects. Those require additional backends and platform integration work.
