"""Platform adapters, translating events and actions in both directions."""
from __future__ import annotations

import inspect
from dataclasses import dataclass, replace

from pythonbots_core.messaggio import Azione, Messaggio, Risposta

CHIAVE_OCCUPATO = "core.occupato"


@dataclass(frozen=True)
class Capacita:
    """What the platform can do, declared rather than discovered by trial."""
    pulsanti: bool = True
    privato: bool = True


def _degrada(a: Azione, c: Capacita) -> Azione:
    """Fit an action into what the platform can do."""
    if a.opzioni and not c.pulsanti:
        return replace(a, opzioni=(), testo_degradato=" · ".join(a.opzioni))
    if a.privata and not c.privato:
        return replace(a, privata=False)
    return a


def _traduci_azione(a: Azione, stringhe) -> Azione:
    """Turn the string key into text; degraded options are appended to the message."""
    if a.testo:
        return a
    testo = stringhe.testo(a.chiave)
    if a.valori:
        try:
            testo = testo.format_map(dict(a.valori))
        except KeyError as e:
            raise KeyError(f"la stringa `{a.chiave}` usa il segnaposto {e} e l'handler non gli ha "
                           f"dato un valore (ha dato: {', '.join(k for k, _ in a.valori)})") from None
    if a.testo_degradato:
        testo = f"{testo}\n{a.testo_degradato}"
    return replace(a, testo=testo)


def _vuole_dati(gestisci) -> bool:
    """Whether the handler asks for data with a third parameter."""
    try:
        return len(inspect.signature(gestisci).parameters) >= 3
    except (TypeError, ValueError):
        return False


def _chiama(registro, gestisci, messaggio, r, deposito) -> None:
    """Call the handler, with data if it asks for it."""
    if not _vuole_dati(gestisci):
        gestisci(messaggio, r)
        return
    from pythonbots_core.dati import Dati
    dich = registro.dichiarazione(messaggio.comando)
    if deposito is None or dich is None:
        nome = dich["nome"] if dich else messaggio.comando
        raise RuntimeError(f"l'handler `{nome}` chiede `dati` (terzo parametro di `gestisci`), "
                           f"ma questo cammino non ha un deposito"
                           + ("" if dich else " ne' una dichiarazione"))
    gestisci(messaggio, r, Dati(deposito, dich, registro.dichiarazioni(), messaggio.mittente))


def instrada(registro, messaggio: Messaggio, capacita: Capacita, stringhe,
             battito=None, deposito=None) -> list[Azione]:
    """One event to the actions already fitted to the platform's capabilities."""
    gestisci = registro.cerca(messaggio.comando)
    if gestisci is None:
        return []
    if battito is not None:
        battito.ricevuto()
    r = Risposta()
    try:
        _chiama(registro, gestisci, messaggio, r, deposito)
    except Exception as e:                                  # noqa: BLE001 — si rilancia tutto il resto
        from pythonbots_core.deposito import occupato
        if not occupato(e):
            raise
        r = Risposta()
        r.privata(CHIAVE_OCCUPATO)
        return [_traduci_azione(_degrada(a, capacita), stringhe) for a in r.azioni]
    azioni = [_traduci_azione(_degrada(a, capacita), stringhe) for a in r.azioni]
    if battito is not None:
        battito.riuscito()
    return azioni
