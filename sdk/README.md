<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 henxnomercy -->

# RANCAGE SDK extension contract (draft)

This document is MIT-licensed under `../licenses/SDK-MIT.txt`.

## Current status

This directory currently contains this draft extension contract only. There is
not yet a stable external backend ABI, a production SDK package, or a supported
third-party backend interface. Do not treat this draft as a compatibility
promise.

## Planned extension contract

Future backend packages should provide:

- A target identifier and supported RANCAGE language/IR versions.
- A capability manifest (types, standard-library APIs, host imports,
  limitations, and security properties).
- A compiler entry point from RANCAGE IR to target artifacts.
- Diagnostics with source locations.
- A conformance test suite.
- Documentation for toolchain versions, build flags, permissions, and
  packaging.

The SDK boundary and compatibility guarantees must be reviewed before the
first stable SDK release.
