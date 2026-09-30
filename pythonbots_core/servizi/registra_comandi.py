"""Register the bot's commands with Discord, from the same registry the endpoint routes with."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


from pythonbots_core.instradamento import Registro  # noqa: E402

API = "https://discord.com/api/v10"


def _chiedi(metodo: str, percorso: str, token: str, corpo=None):
    dati = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(f"{API}{percorso}", data=dati, method=metodo)
    req.add_header("Authorization", f"Bot {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "pythonbots-core (deploy/registra_comandi.py)")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")
        if e.code == 403 and "50001" in corpo and "/guilds/" in percorso:
            sys.exit(
                f"⛔ 403 Missing Access su {percorso}\n"
                f"   L'applicazione non e' autorizzata in quel server. Registrare comandi\n"
                f"   di guild richiede che sia stata INSTALLATA li' — creare il server e\n"
                f"   copiarne l'ID non basta.\n\n"
                f"   Installa con (scope minimo, zero permessi):\n"
                f"   https://discord.com/oauth2/authorize"
                f"?client_id={os.environ.get('DISCORD_APPLICATION_ID', '<app-id>')}"
                f"&scope=applications.commands\n")
        sys.exit(f"⛔ Discord ha risposto {e.code}: {corpo}")


def comandi_dalle_dichiarazioni(handlers: Path, core: Path | None = None) -> list[dict]:
    """One command for every trigger the registry actually routes, with its options."""
    from pythonbots_core import cartella
    from pythonbots_core.about import registra
    from pythonbots_core.opzioni import per_discord, problemi
    from pythonbots_core.stringhe import carica
    registro = Registro.da_cartella(handlers)
    file_di_handler = [p for p in Path(handlers).glob("*.py") if not p.stem.startswith("_")]
    if file_di_handler and not registro.dichiarazioni():
        return []
    sbagliate = [f"{d['nome']}: {p}" for d in registro.dichiarazioni() for p in problemi(d)]
    if sbagliate:
        sys.exit("⛔ opzioni non valide, non registro niente:\n  " + "\n  ".join(sbagliate))
    stringhe = carica(Path(handlers).parent / "strings", os.environ.get("LINGUA", "it"))
    registra(registro, Path(core) if core else cartella())
    from pythonbots_core.diritti import registra as registra_diritti
    registra_diritti(registro)
    fuori = []
    for trigger, handler in registro.comandi():
        nome = trigger.lstrip("/")
        try:
            opzioni = per_discord(registro.opzioni(trigger), stringhe)
        except ValueError as e:
            sys.exit(f"⛔ /{nome}: {e}")
        fuori.append({
            "name": nome,
            "type": 1,
            "description": f"{nome} — handler {handler}",
            **({"options": opzioni} if opzioni else {}),
        })
    return fuori


def main(handlers: Path) -> int:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    app = os.environ.get("DISCORD_APPLICATION_ID")
    if not token or not app:
        sys.exit("FATAL: servono DISCORD_BOT_TOKEN e DISCORD_APPLICATION_ID nell'ambiente.")

    guild = None
    if "--guild" in sys.argv:
        guild = sys.argv[sys.argv.index("--guild") + 1]
    base = f"/applications/{app}/guilds/{guild}/commands" if guild \
        else f"/applications/{app}/commands"

    if "--elenca" in sys.argv:
        for c in _chiedi("GET", base, token) or []:
            print(f"  /{c['name']}  — {c.get('description', '')}")
        return 0

    comandi = comandi_dalle_dichiarazioni(handlers)
    if not comandi:
        sys.exit("⛔ nessun comando dichiarato: mi fermo. Un PUT vuoto li cancellerebbe tutti.")

    _chiedi("PUT", base, token, comandi)
    dove = f"nel server {guild} — **immediati**" if guild else "globali — fino a un'ora"
    print(f"✅ {len(comandi)} comandi registrati, {dove}:")
    for c in comandi:
        print(f"  /{c['name']}")
    return 0
