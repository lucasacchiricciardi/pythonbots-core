"""The Discord interactions endpoint; signature, routing, public heartbeat, one-time download links."""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


from pythonbots_core.adapters.discord import Discord, FirmaNonValida, corpo_http  # noqa: E402
from pythonbots_core.battito import NOME_FILE, Battito  # noqa: E402
from pythonbots_core.deposito import Deposito, avvia  # noqa: E402
from pythonbots_core import cartella  # noqa: E402
from pythonbots_core.instradamento import Registro  # noqa: E402
from pythonbots_core.manifesto import riga_di_avvio  # noqa: E402
from pythonbots_core.stringhe import carica as carica_stringhe  # noqa: E402

RICHIESTE = ("DISCORD_PUBLIC_KEY", "PB_CHIAVE_DATI")

LIMITE_SECONDI = 3

PERCORSO_INTERAZIONI = "/api/interactions"

PERCORSO_BATTITO = "/api/battito"

PERCORSO_COPIA = "/api/copia/"

TESTATE_COPIA = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                 "X-Content-Type-Options": "nosniff", "X-Robots-Tag": "noindex",
                 "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'"}

FORMA_URL_PUBBLICO = r"https://[a-z0-9]([a-z0-9.-]*[a-z0-9])?(:[0-9]{1,5})?/?"


def _ambiente() -> dict:
    mancanti = [v for v in RICHIESTE if not os.environ.get(v)]
    if mancanti:
        sys.exit(f"FATAL: mancano le variabili d'ambiente {mancanti}. "
                 f"Si copiano da `.env.example` e si riempiono sulla macchina: "
                 f"non hanno default, e un default sarebbe peggio della loro assenza.")
    return {v: os.environ[v] for v in RICHIESTE}


def _annota(corpo: bytes, esito: str) -> None:
    """One log line per interaction; what arrived and how it ended, never who."""
    try:
        tipo = json.loads(corpo).get("type", "?")
    except Exception:                                    # noqa: BLE001
        tipo = "?"
    print(f"interazione type={tipo} · {esito}", flush=True)


def crea_gestore(adattatore: Discord, registro: Registro, stringhe, battito, db: Path):
    """The request handler class, bound to the adapter, the registry and the database."""

    class Gestore(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _percorso(self) -> str:
            """The request path without query string and without a trailing slash."""
            return self.path.split("?", 1)[0].rstrip("/") or "/"

        def do_POST(self) -> None:
            if self.path.startswith(PERCORSO_COPIA):
                self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
                return self._scarica(self.path[len(PERCORSO_COPIA):].split("?", 1)[0])
            if self._percorso() != PERCORSO_INTERAZIONI:
                self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
                self._rispondi(404, {"error": "not found"})
                return
            corpo = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
            try:
                with Deposito(db) as deposito:
                    risposta = adattatore.ricevi(registro, corpo, self.headers,
                                                 stringhe, battito, deposito)
            except FirmaNonValida:
                _annota(corpo, "firma non valida")
                self._rispondi(401, {"error": "invalid request signature"})
                return
            except Exception as e:                      # noqa: BLE001
                _annota(corpo, f"errore {type(e).__name__}: {e}")
                self._rispondi(500, {"error": "internal error"})
                return
            _annota(corpo, "ok")
            self._rispondi(200, risposta)

        def do_GET(self) -> None:
            """The heartbeat; whether the bot did its work, not only whether it runs."""
            if self.path.startswith(PERCORSO_COPIA):
                return self._manda(200, _pagina(stringhe.testo("core.copia-titolo"),
                                                stringhe.testo("core.copia-spiegazione"),
                                                stringhe.testo("core.copia-pulsante")),
                                   "text/html; charset=utf-8", TESTATE_COPIA)
            if self._percorso() != PERCORSO_BATTITO:
                self._rispondi(404, {"error": "not found"})
                return
            from pythonbots_core.programma import ultimi
            extra = {}
            try:
                with Deposito(db) as d:
                    extra["lavori"] = {k: v.isoformat(timespec="seconds") for k, v in ultimi(d).items()}
            except Exception as e:                          # noqa: BLE001
                extra["lavori"] = None
                extra["lavori_errore"] = f"{type(e).__name__}: {e}"
            self._rispondi(200, {"stato": "vivo", "limite_secondi": LIMITE_SECONDI,
                                 "interazioni": PERCORSO_INTERAZIONI,
                                 **battito.stato(), **extra})

        def _scarica(self, token: str) -> None:
            """Use up the link and send the copy; the same 404 for every invalid link."""
            from pythonbots_core import copie
            from pythonbots_core.diritti import copia_json, esporta
            with Deposito(db) as d:
                persona = copie.consuma(d, token)
                contenuto = copia_json(esporta(d, registro.dichiarazioni(), persona)) if persona else None
            if contenuto is None:
                print("copia · link non valido", flush=True)
                return self._manda(404, _pagina(stringhe.testo("core.copia-titolo"),
                                                stringhe.testo("core.copia-non-valida"), None),
                                   "text/html; charset=utf-8", TESTATE_COPIA)
            print("copia · scaricata", flush=True)
            self._manda(200, contenuto, "application/json; charset=utf-8",
                        {**TESTATE_COPIA, "Content-Disposition": 'attachment; filename="i-miei-dati.json"'})

        def _manda(self, codice: int, dati: bytes, tipo: str, testate: dict) -> None:
            self.send_response(codice)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dati)))
            for k, v in testate.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(dati)

        def _rispondi(self, codice: int, corpo: dict) -> None:
            dati, tipo = corpo_http(corpo)
            self.send_response(codice)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)

    return Gestore


def _pretendi_scrivibile(dati: Path) -> None:
    """Stop at start-up if the data folder cannot be written."""
    prova = dati / ".prova-scrittura"
    try:
        prova.write_text("", encoding="utf-8")
        prova.unlink()
    except OSError as e:
        sys.exit(f"FATAL: `{dati}` non e' scrivibile da uid {os.getuid()} "
                 f"({type(e).__name__}). Il battito e il deposito non potrebbero "
                 f"salvare niente, e il bot sembrerebbe sano. Se e' un bind mount, il "
                 f"proprietario si aggiusta SULL'HOST:\n"
                 f"  docker run --rm -v <host-path>:/d alpine:3 chown {os.getuid()}:{os.getgid()} /d")


def _pagina(titolo: str, testo: str, pulsante: str | None) -> bytes:
    """A minimal HTML page with no external resources; with the button that posts, when given."""
    from html import escape
    modulo = (f'<form method="post"><button type="submit">{escape(pulsante)}</button></form>'
              if pulsante else "")
    return (f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{escape(titolo)}</title></head>'
            f'<body style="font-family:sans-serif;max-width:32rem;margin:3rem auto;padding:0 1rem">'
            f'<h1>{escape(titolo)}</h1><p>{escape(testo)}</p>{modulo}</body></html>').encode("utf-8")


def righe_di_avvio(albero: Path, porta: int, registro: Registro, stringhe, battito) -> list[str]:
    """The lines the bot logs before listening, in order."""
    return [
        riga_di_avvio(cartella(), albero),
        f"endpoint in ascolto su :{porta} · {len(registro._per_trigger)} comandi "
        f"instradati · {len(stringhe.chiavi())} stringhe in `{stringhe.lingua}` · "
        f"limite di Discord: {LIMITE_SECONDI}s · battito in `{battito.percorso}`",
    ]


def prepara(albero: Path, amb: dict) -> tuple:
    """Everything the handler uses, wired as in production, without the server."""
    try:
        registro = Registro.da_albero(albero)
    except RuntimeError as e:
        sys.exit(f"FATAL: {e}")
    adattatore = Discord(amb["DISCORD_PUBLIC_KEY"])
    stringhe = carica_stringhe(albero / "bot" / "strings", os.environ.get("LINGUA", "it"))

    if (mancanti := stringhe.mancanti(registro.chiavi_stringhe())):
        sys.exit(f"FATAL: queste chiavi sono dichiarate dagli handler e non tradotte in "
                 f"`{stringhe.lingua}`: {mancanti}. Si aggiungono in "
                 f"`bot/strings/{stringhe.lingua}.yaml`.")

    import re
    url = os.environ.get("PB_URL_PUBBLICO", "")
    if url and not re.fullmatch(FORMA_URL_PUBBLICO, url):
        sys.exit(f"FATAL: PB_URL_PUBBLICO={url!r} non e' un indirizzo `https://host` senza percorso: e' la "
                 f"base dei link con cui le persone scaricano la copia dei propri dati.")

    if os.environ.get("DISCORD_BOT_TOKEN"):
        sys.exit("FATAL: DISCORD_BOT_TOKEN e' nell'ambiente dell'endpoint, che e' esposto a internet e non "
                 "lo usa. In `deploy/compose.yml` il servizio `bot` lo svuota; i comandi si registrano con "
                 "`docker compose exec lavori python3 deploy/registra_comandi.py`.")

    dati = Path(os.environ.get("PB_DATI", albero / "data"))
    dati.mkdir(parents=True, exist_ok=True)
    _pretendi_scrivibile(dati)
    battito = Battito(dati / NOME_FILE)
    db = dati / "bot.db"
    avvia(albero, db)
    return registro, adattatore, stringhe, battito, db


def main(albero: Path) -> None:
    amb = _ambiente()
    porta = int(os.environ.get("PORTA", "8080"))
    registro, adattatore, stringhe, battito, db = prepara(albero, amb)
    for riga in righe_di_avvio(albero, porta, registro, stringhe, battito):
        print(riga, flush=True)
    ThreadingHTTPServer(("", porta),
                        crea_gestore(adattatore, registro, stringhe,
                                     battito, db)).serve_forever()
