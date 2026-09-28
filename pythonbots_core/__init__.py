"""The PythonBots core. Use licence; see the LICENSE-ADDENDUM of your order."""
from __future__ import annotations

from pathlib import Path


def cartella() -> Path:
    """The package directory, wherever it is installed."""
    return Path(__file__).resolve().parent


def _versione() -> str:
    """The `versione:` field of VERSION, or `0.0.0` when the file is missing or silent."""
    try:
        for riga in (cartella() / "VERSION").read_text(encoding="utf-8").splitlines():
            chiave, sep, valore = riga.partition(":")
            if sep and chiave.strip() == "versione":
                return valore.strip() or "0.0.0"
    except OSError:
        pass
    return "0.0.0"


__version__ = _versione()
