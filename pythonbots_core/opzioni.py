"""Slash-command options; what a handler declares, and how it becomes the Discord registration."""
from __future__ import annotations

import re

TIPI = {"testo": 3, "intero": 4, "booleano": 5, "utente": 6}

SOTTOCAMPI = ("nome", "tipo", "obbligatoria", "descrizione")

NOME = re.compile(r"^[a-z0-9_-]{1,32}$")

MASSIMO = 25

LUNGHEZZA_DESCRIZIONE = 100


def problemi(d: dict) -> list[str]:
    """The problems of a declaration's options field; empty when it is absent or fine."""
    if "opzioni" not in d:
        return []
    opz = d["opzioni"]
    if not isinstance(opz, dict):
        return ["campo opzioni: una mappa comando → elenco di opzioni"]
    p: list[str] = []
    trigger = set(d.get("trigger") or [])
    chiavi = set(d.get("chiavi_stringhe") or [])
    for comando, voci in opz.items():
        if comando not in trigger:
            p.append(f"campo opzioni: {comando} non e' fra i trigger dell'handler")
            continue
        if not isinstance(voci, list):
            p.append(f"campo opzioni[{comando}]: un elenco")
            continue
        if len(voci) > MASSIMO:
            p.append(f"campo opzioni[{comando}]: al massimo {MASSIMO} opzioni, sono {len(voci)}")
        visti: set[str] = set()
        facoltativa_vista = False
        for i, o in enumerate(voci):
            dove = f"campo opzioni[{comando}][{i}]"
            if not isinstance(o, dict):
                p.append(f"{dove}: una mappa")
                continue
            for s in SOTTOCAMPI:
                if s not in o:
                    p.append(f"{dove}: manca {s}")
            for k in o:
                if k not in SOTTOCAMPI:
                    p.append(f"{dove}: sottocampo sconosciuto {k}")
            nome = o.get("nome")
            if "nome" in o and not (isinstance(nome, str) and NOME.match(nome)):
                p.append(f"{dove}.nome: minuscole, cifre, _ e -, da 1 a 32 caratteri")
            elif nome in visti:
                p.append(f"{dove}.nome: nomi doppi ({nome})")
            visti.add(nome)
            if "tipo" in o and o["tipo"] not in TIPI:
                p.append(f"{dove}.tipo: uno fra {', '.join(TIPI)}")
            if "obbligatoria" in o:
                if not isinstance(o["obbligatoria"], bool):
                    p.append(f"{dove}.obbligatoria: vero o falso (booleano, non testo)")
                elif o["obbligatoria"] and facoltativa_vista:
                    p.append(f"{dove}: le opzioni obbligatorie vanno prima delle facoltative (Discord)")
                elif not o["obbligatoria"]:
                    facoltativa_vista = True
            if "descrizione" in o and o["descrizione"] not in chiavi:
                p.append(f"{dove}.descrizione: una chiave di stringa dichiarata in chiavi_stringhe")
    return p


def per_discord(voci: list[dict], stringhe) -> list[dict]:
    """A command's options in Discord's registration form, descriptions translated."""
    fuori = []
    for o in voci:
        descrizione = stringhe.testo(o["descrizione"]).strip()
        if not 1 <= len(descrizione) <= LUNGHEZZA_DESCRIZIONE:
            raise ValueError(f"la descrizione `{o['descrizione']}` ha {len(descrizione)} caratteri: "
                             f"Discord ne accetta da 1 a {LUNGHEZZA_DESCRIZIONE}")
        fuori.append({"type": TIPI[o["tipo"]], "name": o["nome"], "description": descrizione,
                      "required": o["obbligatoria"]})
    return fuori
