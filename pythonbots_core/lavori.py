"""The scheduled-jobs round; what is due now, run it, send what it writes, remember it."""
from __future__ import annotations

from datetime import timedelta

from pythonbots_core.adapters import _traduci_azione
from pythonbots_core.dati import Dati
from pythonbots_core.messaggio import Risposta
from pythonbots_core.programma import chiave, dovuto, registra, ultimi

RIPROVA = timedelta(minutes=5)


def _esegui(registro, deposito, stringhe, config, handler, voce, lavora, invia) -> None:
    dich = next(d for d in registro.dichiarazioni() if d["nome"] == handler)
    r = Risposta()
    lavora(voce["nome"], r, Dati(deposito, dich, registro.dichiarazioni()))
    testi = []
    for a in r.azioni:
        if a.privata or a.opzioni or a.allegato:
            raise ValueError(f"`{a.chiave}`: da un lavoro esce solo testo in un canale (`risposta.testo`)")
        testi.append(_traduci_azione(a, stringhe).testo)
    if testi and not voce.get("canale"):
        raise ValueError("il lavoro ha scritto un messaggio ma non dichiara un canale")
    for t in testi:
        invia(config["canali"][voce["canale"]], t)


def giro(registro, deposito, stringhe, config: dict, adesso, invia, falliti: dict) -> list[tuple[str, str]]:
    """Run the jobs due now; returns (key, outcome) for each job run."""
    fuso = None
    if (config or {}).get("fuso_orario"):
        from zoneinfo import ZoneInfo
        fuso = ZoneInfo(config["fuso_orario"])
    fatti = ultimi(deposito)
    esiti: list[tuple[str, str]] = []
    for handler, voce, lavora in registro.lavori():
        k = chiave(handler, voce["nome"])
        if k in falliti and adesso - falliti[k] < RIPROVA:
            continue
        if not dovuto(voce, fatti.get(k), adesso, fuso):
            continue
        try:
            _esegui(registro, deposito, stringhe, config, handler, voce, lavora, invia)
        except Exception as e:                              # noqa: BLE001 — un lavoro non ferma gli altri
            falliti[k] = adesso
            esiti.append((k, f"errore {type(e).__name__}: {e}"))
            continue
        registra(deposito, k, adesso)
        falliti.pop(k, None)
        esiti.append((k, "ok"))
    return esiti
