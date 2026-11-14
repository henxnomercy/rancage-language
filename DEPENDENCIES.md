# RANCAGE Dependencies and Standalone Status

## Source development

The active compiler, CLI, and reference VM use Python 3.10+ and the Python standard library. The current source-based developer workflow requires Python. No third-party Python runtime library is needed to run RANCAGE from source.

## Standalone Windows build

`requirements-build.txt` pins PyInstaller 6.22.3. This is a **build-time-only** dependency used to bundle RANCAGE together with the CPython runtime. It is not required by end users.

The Windows distribution contains the interpreter/runtime files required by the packaged application. End users can run the bundle without separately installing Python.

## Dependency distinctions

| Use case | Python installed separately? | PyInstaller installed? |
|---|---:|---:|
| Run RANCAGE from source | Yes | No |
| Develop RANCAGE compiler | Yes | No |
| Build Windows executable | Yes | Yes, build-time only |
| Run packaged `cage.exe` | No | No |
| Run `.rcb` through packaged RANCAGE VM | No | No |

## What standalone does not mean

PyInstaller bundles a Python interpreter and RANCAGE together. The resulting executable is not a native rewrite of the compiler. Python remains embedded in the distribution. This does not implement self-hosting.

PyInstaller must be run on the target operating system to build for that OS; it is not a cross-compiler. The current preview builds Windows x64 only.
