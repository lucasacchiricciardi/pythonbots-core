"""People's rights on the bot's data; table ownership, export and deletion."""
from __future__ import annotations

PERSONA = "persona"


def possiede(dich: dict, tabella: str) -> bool:
    """A handler owns the tables named after it or starting with its name and an underscore."""
    n = dich["nome"]
    return tabella == n or tabella.startswith(n + "_")


def _campi(dich: dict) -> set[str]:
    return {v["campo"] for v in dich.get("dati_memorizzati", [])}


def tabelle_dell_handler(deposito, dich: dict) -> list[str]:
    return sorted(t for t in deposito.tabelle() if possiede(dich, t))


def esporta(deposito, dichiarazioni: list[dict], persona: str) -> dict[str, list[dict]]:
    """Everything the bot keeps on this person, declared fields only."""
    fuori: dict[str, list[dict]] = {}
    for d in dichiarazioni:
        campi = _campi(d)
        if PERSONA not in campi:
            continue
        for t in tabelle_dell_handler(deposito, d):
            colonne = sorted(campi & deposito.colonne(t))
            if not colonne:
                continue
            righe = deposito.leggi(
                f"SELECT {', '.join(colonne)} FROM {t} WHERE {PERSONA} = ?", (persona,))
            if righe:
                fuori.setdefault(t, []).extend(dict(zip(colonne, r)) for r in righe)
    return fuori


def cancella(deposito, dichiarazioni: list[dict], persona: str) -> dict[str, int]:
    """Delete this person's rows; rows removed, by table."""
    fatto: dict[str, int] = {}
    for d in dichiarazioni:
        if PERSONA not in _campi(d):
            continue
        for t in tabelle_dell_handler(deposito, d):
            if PERSONA not in deposito.colonne(t):
                continue
            quante = len(deposito.leggi(
                f"SELECT 1 FROM {t} WHERE {PERSONA} = ?", (persona,)))
            if quante:
                deposito.esegui(f"DELETE FROM {t} WHERE {PERSONA} = ?", (persona,))
                fatto[t] = quante
    deposito.conferma()
    return fatto
