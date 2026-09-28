"""Platform adapters, translating events and actions in both directions."""
from __future__ import annotations

from dataclasses import dataclass

from pythonbots_core.messaggio import Azione, Messaggio, Risposta


@dataclass(frozen=True)
class Capacita:
    """What the platform can do, declared rather than discovered by trial."""
    pulsanti: bool = True
    privato: bool = True


def _degrada(a: Azione, c: Capacita) -> Azione:
    """Fit an action into what the platform can do."""
    if a.opzioni and not c.pulsanti:
        return Azione(a.chiave, privata=a.privata, opzioni=(),
                      testo_degradato=" · ".join(a.opzioni))
    if a.privata and not c.privato:
        return Azione(a.chiave, privata=False, opzioni=a.opzioni,
                      testo_degradato=a.testo_degradato)
    return a


def _traduci_azione(a: Azione, stringhe) -> Azione:
    """Turn the string key into text; degraded options are appended to the message."""
    if a.testo:
        return a
    testo = stringhe.testo(a.chiave)
    if a.testo_degradato:
        testo = f"{testo}\n{a.testo_degradato}"
    return Azione(a.chiave, privata=a.privata, opzioni=a.opzioni,
                  testo_degradato=a.testo_degradato, testo=testo)


def instrada(registro, messaggio: Messaggio, capacita: Capacita, stringhe,
             battito=None) -> list[Azione]:
    """One event to the actions already fitted to the platform's capabilities."""
    gestisci = registro.cerca(messaggio.comando)
    if gestisci is None:
        return []
    if battito is not None:
        battito.ricevuto()
    r = Risposta()
    gestisci(messaggio, r)
    azioni = [_traduci_azione(_degrada(a, capacita), stringhe) for a in r.azioni]
    if battito is not None:
        battito.riuscito()
    return azioni
