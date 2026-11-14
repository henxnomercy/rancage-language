"""PyInstaller entry point for the RANCAGE command-line application."""
from rancage.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
