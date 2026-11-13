"""PyInstaller entry point for the NOVA command-line application."""
from nova.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
