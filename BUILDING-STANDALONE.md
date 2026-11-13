# Building NOVA Standalone for Windows

## Purpose

This process bundles the NOVA CLI and the Python runtime into Windows executables. End users do not need a separate Python installation. The compiler implementation itself remains Python.

## Requirements

- Windows x64 build host (local Windows PC or GitHub Actions Windows runner).
- Python 3.10 or newer. Python 3.14 is supported by the pinned PyInstaller release.
- Internet access during build to install the build-only PyInstaller dependency.

PyInstaller is not a cross-compiler. Build a Windows executable on Windows, a Linux executable on Linux, and a macOS executable on macOS.

## Local build

Open PowerShell at the repository root:

```powershell
python --version
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
.\build-windows.ps1
.\test-bundle.ps1
```

Outputs:

- `dist\nova-windows-x64.exe` — single-file executable.
- `dist\nova-windows-x64.zip` — complete distribution including the one-folder fallback and examples.
- `dist\SHA256SUMS.txt` — SHA-256 hashes.

## GitHub Actions build

Push commits to `feature/windows-standalone` or `main` to trigger the workflow automatically when relevant files change. A pull request targeting `main` also triggers it. The workflow supports manual execution using **Actions → NOVA Windows Standalone Build → Run workflow** (select the feature branch). A successful run uploads an artifact named `nova-windows-x64-standalone-preview` for 30 days.

## Test a built executable

```powershell
.\dist\onefile\nova.exe --version
.\dist\onefile\nova.exe check examples\hello.nova
.\dist\onefile\nova.exe run examples\hello.nova
```

The automated smoke-test script checks both the one-file and one-folder variants, including building and running a `.nvm` file.

## One-file vs one-folder

- One-file is easier to distribute. Its first launch can be slower because it extracts bundled files to a temporary directory. Some endpoint security products may inspect or quarantine newly built executables.
- One-folder keeps runtime files beside `nova.exe`, often starts faster, and is a fallback if one-file distribution causes problems. Keep the complete folder together.

## Important limitation

A PyInstaller executable still contains the Python interpreter/runtime. It removes the end user's separate Python installation requirement; it does not make NOVA a native machine-code compiler or a self-hosting language. The `.nvm` program still runs on the NOVA VM included in the bundle.
