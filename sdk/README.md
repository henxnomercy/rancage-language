# NOVA SDK extension contract (draft)

This directory is the planned open extension surface. In 0.1 it contains the SDK policy only; there is not yet a stable external backend ABI.

Future backend packages should provide:

- A target identifier and supported NOVA language/IR versions.
- A capability manifest (types, standard-library APIs, host imports, limitations).
- A compiler entry point from NOVA IR to target artifacts.
- Diagnostics with source locations.
- A conformance test suite.
- Documentation for toolchain versions, build flags, permissions, and packaging.

Files explicitly designated as SDK materials are intended to use the MIT license in `../licenses/SDK-MIT.txt`. The compiler/runtime core remains under its separately designated license. The exact boundary must be finalized before stable release.
