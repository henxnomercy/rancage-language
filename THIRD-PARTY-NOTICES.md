# Third-Party Notices — RANCAGE Windows Standalone Preview

The standalone build bundles the CPython interpreter/runtime and the PyInstaller bootloader.

- Python is distributed under the Python Software Foundation (PSF) license. See https://docs.python.org/3/license.html. The build script copies the Windows Python `LICENSE.txt` into the distribution when that file is present in the selected Python installation.
- PyInstaller is licensed under GPL-2.0-or-later. Its bootloader and related files embedded in the final executable carry the PyInstaller Bootloader Exception; its runtime hooks are Apache-2.0. The build script copies PyInstaller’s `COPYING.txt` into the package when it is exposed by installed package metadata. The authoritative license is at https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt; review it before redistributing the bundled build.

RANCAGE's own core and SDK notices remain in `licenses/`. Bundling does not change the license or ownership of RANCAGE itself. This notice is informational and is not legal advice.
