"""PyInstaller entry shim for the production PackLab Studio application."""

from packlab_studio.app import main

if __name__ == "__main__":
    raise SystemExit(main())
