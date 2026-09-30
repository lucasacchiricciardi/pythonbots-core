"""Scheduled jobs; what a handler declares, what start-up needs, and when each one is due."""
from __future__ import annotations

import re

GIORNI = ("lun", "mar", "mer", "gio", "ven", "sab", "dom")

SOTTOCAMPI = ("nome", "ogni_minuti", "alle", "giorni", "canale")

NOME = re.compile(r"^[a-z][a-z0-9_]*$")
NOME_CANALE = re.compile(r"^[a-z][a-z0-9_-]*$")
ORA = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")

ID_CANALE = re.compile(r"^[0-9]{17,20}$")

MINUTI_MIN, MINUTI_MAX = 1, 7 * 24 * 60


def problemi(d: dict) -> list[str]:
    """The problems of the schedule and of its consistency with lavoro; empty when fine."""
    p: list[str] = []
    if "programma" not in d:
        return p
    if d.get("lavoro") is not True:
        p.append("campo lavoro: con un programma dev'essere vero")
    prog = d["programma"]
    if not isinstance(prog, list) or not prog:
        p.append("campo programma: un elenco non vuoto di lavori")
        return p
    visti: set = set()
    for i, v in enumerate(prog):
        dove = f"campo programma[{i}]"
        if not isinstance(v, dict):
            p.append(f"{dove}: una mappa")
            continue
        for k in v:
            if k not in SOTTOCAMPI:
                p.append(f"{dove}: sottocampo sconosciuto {k}")
        nome = v.get("nome")
        if not (isinstance(nome, str) and NOME.match(nome)):
            p.append(f"{dove}.nome: minuscolo, cifre e underscore, iniziale alfabetica")
        elif nome in visti:
            p.append(f"{dove}.nome: nomi doppi ({nome})")
        visti.add(nome)
        if ("ogni_minuti" in v) == ("alle" in v):
            p.append(f"{dove}: uno fra `ogni_minuti` e `alle`, esattamente uno")
        if "ogni_minuti" in v:
            m = v["ogni_minuti"]
            if type(m) is not int or not MINUTI_MIN <= m <= MINUTI_MAX:
                p.append(f"{dove}.ogni_minuti: un intero da {MINUTI_MIN} a {MINUTI_MAX}")
            if "giorni" in v:
                p.append(f"{dove}.giorni: solo con `alle`")
        if "alle" in v and not (isinstance(v["alle"], str) and ORA.match(v["alle"])):
            p.append(f"{dove}.alle: un'ora HH:MM, da 00:00 a 23:59")
        if "giorni" in v:
            g = v["giorni"]
            if not isinstance(g, list) or not g or any(x not in GIORNI for x in g):
                p.append(f"{dove}.giorni: un elenco non vuoto fra {', '.join(GIORNI)}")
        if "canale" in v and not (isinstance(v["canale"], str) and NOME_CANALE.match(v["canale"])):
            p.append(f"{dove}.canale: un nome, minuscolo; l'id sta in bot/config.yaml")
    return p


def problemi_avvio(registro, config: dict) -> list[str]:
    """What stops the jobs process; a missing lavora, a channel without an id, the time zone."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    p: list[str] = []
    canali = (config or {}).get("canali") or {}
    serve_fuso = False
    for handler, voce, lavora in registro.lavori():
        if not callable(lavora):
            p.append(f"l'handler `{handler}` ha un programma e non ha la funzione `lavora`")
        if "alle" in voce:
            serve_fuso = True
        c = voce.get("canale")
        if c is not None:
            id_ = canali.get(c)
            if not (isinstance(id_, str) and ID_CANALE.match(id_)):
                p.append(f"il canale `{c}` (lavoro {handler}.{voce['nome']}) non ha un id in "
                         f"bot/config.yaml, lavori.canali.{c}: servono le cifre, fra virgolette")
    if serve_fuso:
        fuso = (config or {}).get("fuso_orario")
        try:
            if not isinstance(fuso, str):
                raise ZoneInfoNotFoundError
            ZoneInfo(fuso)
        except (ZoneInfoNotFoundError, ValueError):
            p.append(f"lavori.fuso_orario in bot/config.yaml: serve un fuso come «Europe/Rome» per i "
                     f"lavori «alle» (ora: {fuso!r})")
    return p


def chiave(handler: str, nome: str) -> str:
    """A job's key in core_battito."""
    return f"lavoro:{handler}.{nome}"


def dovuto(voce: dict, ultimo, adesso, fuso) -> bool:
    """Whether the job is due now; a timed job looks only at today's occurrence, in the declared time zone."""
    from datetime import datetime, time, timedelta
    if "ogni_minuti" in voce:
        return ultimo is None or adesso - ultimo >= timedelta(minutes=voce["ogni_minuti"])
    locale = adesso.astimezone(fuso)
    if "giorni" in voce and GIORNI[locale.weekday()] not in voce["giorni"]:
        return False
    ore, minuti = (int(x) for x in voce["alle"].split(":"))
    occorrenza = datetime.combine(locale.date(), time(ore, minuti), tzinfo=fuso)
    return occorrenza <= adesso and (ultimo is None or ultimo < occorrenza)


def ultimi(deposito) -> dict:
    """The last successful run of every job, by key."""
    from datetime import datetime
    return {k: datetime.fromisoformat(v) for k, v in
            deposito.leggi("SELECT chiave, ultimo_lavoro FROM core_battito WHERE chiave LIKE 'lavoro:%'")
            if v}


def registra(deposito, chiave_lavoro: str, quando) -> None:
    """Record a job's successful run; update when the key exists, insert otherwise."""
    valore = quando.isoformat(timespec="seconds")
    n = deposito._c.execute("UPDATE core_battito SET ultimo_lavoro = ? WHERE chiave = ?",
                            (valore, chiave_lavoro)).rowcount
    if n == 0:
        deposito.esegui("INSERT INTO core_battito (chiave, ultimo_lavoro) VALUES (?, ?)",
                        (chiave_lavoro, valore))
    deposito.conferma()
