# NOVA Windows Standalone Preview

This package runs NOVA on Windows without requiring the end user to install Python.

## Two build formats

- `nova.exe`: a single-file executable. It is convenient to copy, but first startup can be slower because the bundled runtime is extracted before execution.
- `portable/nova.exe`: a one-folder build. Keep the entire `portable` folder together when moving it. This can start faster and is a useful fallback if a security product dislikes one-file bundles.

## Commands

Open PowerShell or Command Prompt in this folder:

```powershell
.\nova.exe --version
.\nova.exe check .\examples\hello.nova
.\nova.exe run .\examples\hello.nova
.\nova.exe build .\examples\hello.nova -o .\hello.nvm
.\nova.exe run .\hello.nvm
```

For the one-folder build, use `portable\nova.exe` instead.

## Important distinction

This is a **bundled Python application**, not a native machine-code compiler and not a self-hosting NOVA compiler. PyInstaller packages the NOVA program together with the Python interpreter and required runtime files. The end user does not need a separate Python installation, but Python remains inside the distribution.

NOVA source programs and `.nvm` bytecode are not encrypted by this packaging process. This is a deployment convenience, not an anti-reverse-engineering feature.

## Support status

The first preview targets Windows x64. It must pass the GitHub Actions build and smoke tests before being treated as a supported distribution. macOS and Linux packages must be built on their respective operating systems.
