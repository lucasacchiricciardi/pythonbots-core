"""The scheduled-jobs process; one round every few seconds, in its own container."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


from pythonbots_core.deposito import Deposito  # noqa: E402
from pythonbots_core.instradamento import Registro  # noqa: E402
from pythonbots_core.lavori import giro  # noqa: E402
from pythonbots_core.programma import problemi_avvio  # noqa: E402
from pythonbots_core.stringhe import carica  # noqa: E402

PAUSA = 30

TABELLE = {"core_migrazioni", "core_battito", "migrazioni"}


def invia_discord(token: str):
    """A function that posts text to a channel with the bot token, mentions disabled."""
    def invia(canale: str, testo: str) -> None:
        r = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{canale}/messages", method="POST",
            data=json.dumps({"content": testo, "allowed_mentions": {"parse": []}}).encode(),
            headers={"Authorization": f"Bot {token}", "Content-Type": "application/json",
                     "User-Agent": "DiscordBot (pythonbots-core, lavori)"})
        with urllib.request.urlopen(r, timeout=10) as risposta:
            if not 200 <= risposta.status < 300:
                raise RuntimeError(f"Discord ha risposto {risposta.status}")
    return invia


def leggi_config(albero: Path) -> dict:
    """The lavori section of bot/config.yaml, or empty."""
    import yaml
    f = Path(albero) / "bot" / "config.yaml"
    dati = yaml.safe_load(f.read_text(encoding="utf-8")) if f.is_file() else None
    return (dati or {}).get("lavori") or {}


def prepara(albero: Path, attesa: float = 120) -> tuple:
    """Registry, strings, configuration and database, checked; stops and names what is missing."""
    registro = Registro.da_cartella(Path(albero) / "bot" / "handlers")
    config = leggi_config(albero)
    if (problemi := problemi_avvio(registro, config)):
        sys.exit("FATAL: i lavori programmati non possono partire:\n  " + "\n  ".join(problemi))
    stringhe = carica(Path(albero) / "bot" / "strings", os.environ.get("LINGUA", "it"))
    if (mancanti := stringhe.mancanti(registro.chiavi_stringhe())):
        sys.exit(f"FATAL: chiavi dichiarate e non tradotte in `{stringhe.lingua}`: {mancanti}")
    db = Path(os.environ.get("PB_DATI", Path(albero) / "data")) / "bot.db"
    fine = time.monotonic() + attesa
    while True:
        if db.is_file():
            with Deposito(db) as d:
                if TABELLE <= d.tabelle():
                    break
        if time.monotonic() >= fine:
            sys.exit(f"FATAL: dopo {attesa:g} s in `{db}` non ci sono ancora le migrazioni: le applica "
                     f"l'endpoint all'avvio. Il container del bot e' partito?")
        time.sleep(2)
    return registro, stringhe, config, db


def main(albero: Path) -> None:
    mancanti = [v for v in ("DISCORD_BOT_TOKEN", "PB_CHIAVE_DATI") if not os.environ.get(v)]
    if mancanti:
        sys.exit(f"FATAL: mancano le variabili d'ambiente {mancanti}.")
    registro, stringhe, config, db = prepara(albero)
    lavori = registro.lavori()
    if not lavori:
        print("lavori · nessun lavoro programmato: resto fermo", flush=True)
        while True:
            time.sleep(3600)
    print(f"lavori · {len(lavori)} programmati · un giro ogni {PAUSA} s", flush=True)
    invia = invia_discord(os.environ["DISCORD_BOT_TOKEN"])
    falliti: dict = {}
    while True:
        with Deposito(db) as d:
            for k, esito in giro(registro, d, stringhe, config, datetime.now(timezone.utc), invia, falliti):
                print(f"lavori · {k} · {esito}", flush=True)
        time.sleep(PAUSA)
