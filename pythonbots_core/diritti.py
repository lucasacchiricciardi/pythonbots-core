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


def copia_json(fuori: dict) -> bytes:
    """The copy as JSON, by table, without the pseudonym; one function for the attachment and the link."""
    import json
    pulito = {t: [{k: v for k, v in r.items() if k != PERSONA} for r in righe]
              for t, righe in sorted(fuori.items())}
    return json.dumps(pulito, ensure_ascii=False, indent=2, default=str).encode("utf-8")


DICHIARAZIONE = {
    "nome": "diritti",
    "piattaforme": ["discord"],
    "trigger": ["/i-miei-dati", "/cancellami"],
    "permessi": [],
    "input_esterni": [],
    "dati_memorizzati": [],
    "chiavi_stringhe": ["diritti.copia", "diritti.copia-link", "diritti.copia-troppo-grande",
                        "diritti.cancellato", "diritti.nulla-da-mostrare", "diritti.nulla-da-cancellare"],
    "prese": [],
    "lavoro": False,
}

NOME_COPIA = "i-miei-dati.json"


def _riassunto(fuori: dict) -> str:
    """One line per table with its row count; it goes in the text, the data in the file."""
    return "\n".join(f"- {t}: {len(fuori[t])}" for t in sorted(fuori))


def gestisci(messaggio, risposta, dati):
    """The commands /i-miei-dati and /cancellami, always private."""
    if messaggio.comando == "/cancellami":
        tolte = sum(dati.cancella_i_miei().values())
        if tolte:
            risposta.privata("diritti.cancellato", quante=tolte)
        else:
            risposta.privata("diritti.nulla-da-cancellare")
        return
    fuori = dati.miei_dati()
    if not fuori:
        risposta.privata("diritti.nulla-da-mostrare")
        return
    riassunto, contenuto = _riassunto(fuori), copia_json(fuori)
    if messaggio.limite_allegati and len(contenuto) > messaggio.limite_allegati:
        link = dati.link_mia_copia()
        if link:
            risposta.privata("diritti.copia-link", riassunto=riassunto, link=link)
        else:
            risposta.privata("diritti.copia-troppo-grande", riassunto=riassunto)
        return
    risposta.file("diritti.copia", NOME_COPIA, contenuto, riassunto=riassunto)


def con_i_diritti(dichiarazioni: list) -> list:
    """The delivered bot's declarations; the client's handlers plus the rights one."""
    if any(d.get("nome") == DICHIARAZIONE["nome"] for d in dichiarazioni):
        return list(dichiarazioni)
    return list(dichiarazioni) + [DICHIARAZIONE]


def registra(registro) -> None:
    """Add /i-miei-dati and /cancellami to the registry; stop if a client handler already declares them."""
    for t in DICHIARAZIONE["trigger"]:
        gia = registro.dichiarazione(t)
        if registro.cerca(t) is not None:
            nome = gia["nome"] if gia else "?"
            raise RuntimeError(
                f"l'handler `{nome}` del bot dichiara {t}, che dalla 0.1.8 e' un comando del core: "
                f"togli `bot/handlers/{nome}.py` (vedi la nota di aggiornamento della 0.1.8).")
    registro.aggiungi(DICHIARAZIONE["nome"], DICHIARAZIONE["trigger"], gestisci,
                      DICHIARAZIONE["chiavi_stringhe"], DICHIARAZIONE)
