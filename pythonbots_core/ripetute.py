"""A signed request counts once; the ids of interactions already seen, for a few minutes."""
from __future__ import annotations

import sqlite3

RICORDO = 2 * 300


def gia_vista(deposito, id_interazione: str, ora: float) -> bool:
    """True if the interaction was already seen; otherwise remember it and return False."""
    ora = int(ora)
    deposito.esegui("DELETE FROM core_interazioni WHERE vista < ?", (ora - RICORDO,))
    try:
        deposito.esegui("INSERT INTO core_interazioni (id, vista) VALUES (?, ?)", (str(id_interazione), ora))
    except sqlite3.IntegrityError:
        deposito.conferma()
        return True
    deposito.conferma()
    return False
