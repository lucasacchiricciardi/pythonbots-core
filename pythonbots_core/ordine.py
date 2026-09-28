"""The order file, which says whose delivery this is."""
from __future__ import annotations

from pathlib import Path

import yaml

NOME_FILE = "ordine.yaml"

VARIABILE = "PB_ORDINE"

CAMPI = ("ordine", "licenziatario", "bot", "contatto", "informativa", "team", "applicazione")

CAMPI_NUMERICI = {"team": "di Developer Team", "applicazione": "di applicazione Discord"}

from pythonbots_core.informativa import CAMPI_TITOLARE  # noqa: E402


def problemi(o: dict) -> list[str]:
    """What is missing or has the wrong type, as a list."""
    p: list[str] = []
    if not isinstance(o, dict):
        return [f"l'ordine non e' una mappa: e' {type(o).__name__}"]

    for c in CAMPI:
        v = o.get(c)
        if not isinstance(v, str) or not v.strip():
            p.append(f"manca `{c}`" if v is None else f"`{c}`: deve essere testo non vuoto")

    t = o.get("titolare")
    if not isinstance(t, dict):
        p.append("manca `titolare` (nome, indirizzo, email)")
    else:
        p += [f"titolare: manca `{c}`" for c in CAMPI_TITOLARE
              if not str(t.get(c, "")).strip()]

    for c, cosa in CAMPI_NUMERICI.items():
        if isinstance(v := o.get(c), str) and v.strip() and not v.strip().isdigit():
            p.append(f"`{c}`: {v!r} non e' un id numerico {cosa} (solo cifre). "
                     f"Si legge nel Developer Portal, non e' il nome")
    return p


def carica(percorso: Path) -> dict:
    """The order from its file; raises when it is missing or invalid."""
    p = Path(percorso)
    if not p.is_file():
        raise FileNotFoundError(
            f"l'ordine non c'e': `{p}`.\n"
            f"  Serve un file YAML con questi campi, tutti obbligatori:\n"
            f"    {', '.join(CAMPI)}\n"
            f"    titolare: {{{', '.join(CAMPI_TITOLARE)}}}   (piu' `piva`, opzionale)\n"
            f"  Contiene l'anagrafica del cliente, quindi NON sta nel repo: si scrive sulla\n"
            f"  macchina di consegna, accanto all'albero. Il formato completo, con il perche' di\n"
            f"  ogni campo, e' nella docstring di `pythonbots_core/ordine.py`.")
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    if (guai := problemi(d)):
        raise ValueError(f"l'ordine `{p}` non e' completo:\n" +
                         "\n".join(f"  · {g}" for g in guai))
    return d
