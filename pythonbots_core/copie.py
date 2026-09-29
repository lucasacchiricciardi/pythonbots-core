"""One-time links to download a copy of one's own data, beyond the attachment limit."""
from __future__ import annotations

import hashlib
import re
import secrets
import time

SCADENZA = 15 * 60

_FORMA = re.compile(r"^[A-Za-z0-9_-]{43}$")


def _impronta(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def crea(deposito, persona: str, ora: float | None = None) -> str:
    """A new token for this (pseudonymised) person; removes expired links first."""
    ora = int(time.time() if ora is None else ora)
    token = secrets.token_urlsafe(32)
    deposito.esegui("DELETE FROM core_copie WHERE scade <= ?", (ora,))
    deposito.esegui("INSERT INTO core_copie (impronta, persona, scade, usato) VALUES (?, ?, ?, 0)",
                    (_impronta(token), persona, ora + SCADENZA))
    deposito.conferma()
    return token


def consuma(deposito, token: str, ora: float | None = None) -> str | None:
    """The link's person if the link is valid, and from then on it is not; otherwise None."""
    if not isinstance(token, str) or not _FORMA.match(token):
        return None
    ora = int(time.time() if ora is None else ora)
    imp = _impronta(token)
    n = deposito._c.execute("UPDATE core_copie SET usato = 1 WHERE impronta = ? AND usato = 0 AND scade > ?",
                            (imp, ora)).rowcount
    deposito.conferma()
    if n != 1:
        return None
    return deposito.leggi("SELECT persona FROM core_copie WHERE impronta = ?", (imp,))[0][0]


def cancella_persona(deposito, persona: str) -> None:
    """Remove a person's pending links."""
    deposito.esegui("DELETE FROM core_copie WHERE persona = ?", (persona,))
    deposito.conferma()
