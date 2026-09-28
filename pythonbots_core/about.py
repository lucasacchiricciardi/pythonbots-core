"""The `/about` command, which repeats the start-up line on request."""
from __future__ import annotations

from pathlib import Path

from pythonbots_core.manifesto import about as _about

TRIGGER = "/about"

NOME = "about"

CHIAVE = "pythonbots_core.about"


def registra(registro, core: Path, albero: Path | None = None) -> None:
    """Add `/about` to the registry, bound to the core directory and the delivered tree."""
    core = Path(core)

    def gestisci(messaggio, risposta) -> None:
        risposta.fatto(CHIAVE, _about(core, albero))

    registro.aggiungi(NOME, (TRIGGER,), gestisci)
