"""Platform data at rest; identifiers are pseudonymised with a deployment secret."""
from __future__ import annotations

import hashlib
import hmac
import os

VARIABILE = "PB_CHIAVE_DATI"

LUNGHEZZA = 64


def chiave() -> bytes:
    """The key from the environment; raises when it is missing."""
    valore = os.environ.get(VARIABILE)
    if not valore:
        raise RuntimeError(
            f"{VARIABILE} non e' nell'ambiente. E' la chiave con cui gli identificativi "
            f"Discord diventano pseudonimi: senza, il bot scriverebbe API Data IN CHIARO, "
            f"e i Developer Terms § 5(c) non lo permettono. Niente default: un default "
            f"sarebbe una chiave pubblica.")
    return valore.encode("utf-8")


def pseudonimo(valore) -> str:
    """The identifier in a form that cannot be reversed but can still be compared."""
    return hmac.new(chiave(), str(valore).encode("utf-8"), hashlib.sha256).hexdigest()
