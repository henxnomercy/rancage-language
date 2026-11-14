# Third-Party Notices — RANCAGE Windows Standalone Preview

The Windows standalone distribution bundles the CPython interpreter/runtime and the PyInstaller bootloader. The build process also uses PyInstaller community hooks.

- **CPython:** The bundled Python runtime is distributed under the Python Software Foundation (PSF) license, with other notices as marked by the CPython distribution. The build script requires the Windows Python installation's `LICENSE.txt` (or `LICENSE`) and copies it to `licenses/PYTHON-LICENSE.txt`. See https://docs.python.org/3/license.html.
- **PyInstaller 6.22.3:** PyInstaller is licensed under GPL-2.0-or-later with its Bootloader Exception for the bootloader and related files embedded in the executable. PyInstaller runtime hooks and additional runtime modules identified by its `COPYING.txt` are Apache-2.0. The build script requires and copies the distribution's `COPYING.txt` to `licenses/PYINSTALLER-COPYING.txt`. See https://pyinstaller.org/en/stable/license.html and https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/COPYING.txt.
- **pyinstaller-hooks-contrib 2026.10:** Standard community hooks are GPL-2.0-or-later; runtime hooks are Apache-2.0. The build script requires and copies the installed distribution's `LICENSE` to `licenses/PYINSTALLER-HOOKS-CONTRIB-LICENSE.txt`. See https://github.com/pyinstaller/pyinstaller-hooks-contrib/blob/v2026.10/LICENSE.

RANCAGE's own core and SDK notices remain in `licenses/`. Bundling third-party components does not change the license or ownership of RANCAGE itself. This notice is informational and is not legal advice.
