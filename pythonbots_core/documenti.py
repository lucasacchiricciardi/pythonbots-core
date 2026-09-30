"""Markdown to HTML for the documents this package generates."""
from __future__ import annotations

import html
import re

STILE = """
:root { color-scheme: light dark; }
body { max-width: 42rem; margin: 3rem auto; padding: 0 1.2rem;
       font: 16px/1.65 system-ui, -apple-system, "Segoe UI", sans-serif; }
h1 { font-size: 1.6rem; line-height: 1.25; }
h2 { font-size: 1.15rem; margin-top: 2.4rem; }
hr { border: 0; border-top: 1px solid currentColor; opacity: .18; margin: 2rem 0; }
table { border-collapse: collapse; width: 100%; font-size: .93rem; }
th, td { border: 1px solid currentColor; border-color: color-mix(in srgb, currentColor 22%, transparent);
         padding: .45rem .6rem; text-align: left; vertical-align: top; }
code { font-size: .92em; padding: .1em .35em; border-radius: 3px;
       background: color-mix(in srgb, currentColor 10%, transparent); }
blockquote { margin: 1.2rem 0; padding: .1rem 1rem; border-left: 3px solid currentColor; }
footer { margin-top: 3rem; font-size: .85rem; opacity: .7; }
"""


def _riga(t: str) -> str:
    """Bold, italics, code and links, applied after HTML escaping."""
    t = html.escape(t)
    t = re.sub(r"\[(.+?)\]\((/[^)\s]*)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


def _tabella(righe: list[str]) -> str:
    """A Markdown table; the separator row is skipped."""
    fuori, prima = ["<table>"], True
    for r in righe:
        celle = [c.strip() for c in r.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in celle):
            continue
        tag = "th" if prima else "td"
        fuori.append("<tr>" + "".join(f"<{tag}>{_riga(c)}</{tag}>" for c in celle) + "</tr>")
        prima = False
    return "\n".join(fuori + ["</table>"])


def md_a_html(testo: str, titolo: str) -> str:
    """The document as a single self-contained page with no external resources."""
    corpo, elenco, tabella, citazione, paragrafo = [], [], [], [], []

    def chiudi():
        nonlocal elenco, tabella, citazione, paragrafo
        if paragrafo:
            unito = ""
            for i, riga in enumerate(paragrafo):
                if i:
                    unito += "\x00" if paragrafo[i - 1].endswith(" ") else " "
                unito += riga.rstrip()
            corpo.append("<p>" + _riga(unito).replace("\x00", "<br>\n") + "</p>")
            paragrafo = []
        if elenco:
            corpo.append("<ul>" + "".join(f"<li>{_riga(x)}</li>" for x in elenco) + "</ul>")
            elenco = []
        if tabella:
            corpo.append(_tabella(tabella)); tabella = []
        if citazione:
            corpo.append("<blockquote>" + " ".join(_riga(x) for x in citazione)
                         + "</blockquote>")
            citazione = []

    for r in testo.splitlines():
        s = r.strip()
        if s.startswith(("|", "> ", "- ")) and paragrafo:
            chiudi()
        if s.startswith("|"):
            tabella.append(s); continue
        if s.startswith("> "):
            citazione.append(s[2:]); continue
        if s.startswith("- "):
            elenco.append(s[2:]); continue
        if elenco and not paragrafo and r.startswith("  ") and s:
            elenco[-1] += " " + s; continue
        if not s:
            chiudi()
            continue
        if s.startswith("## ") or s.startswith("# ") or (set(s) == {"-"} and len(s) >= 3):
            chiudi()
        if s.startswith("## "):
            corpo.append(f"<h2>{_riga(s[3:])}</h2>")
        elif s.startswith("# "):
            corpo.append(f"<h1>{_riga(s[2:])}</h1>")
        elif set(s) == {"-"} and len(s) >= 3:
            corpo.append("<hr>")
        else:
            paragrafo.append(s + " " if r.rstrip("\n").endswith("  ") else s)
    chiudi()

    return (f'<!doctype html>\n<html lang="it">\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f"<title>{html.escape(titolo)}</title>\n<style>{STILE}</style>\n"
            + "\n".join(corpo)
            + "\n<footer>Documento generato dalle dichiarazioni degli handler del bot: "
              "cambia insieme al codice.</footer>\n</html>\n")


PAGINE = {"informativa": "Informativa privacy", "supporto": "Supporto", "termini": "Termini di servizio"}

MODELLO_TERMINI = ("bot", "documenti", "termini.md")


def indice(nome_app: str, pagine: dict[str, str]) -> str:
    """The index page served at the root."""
    righe = [f"# {nome_app}", "",
             "I documenti pubblici di questa applicazione Discord.", ""]
    righe += [f"- [{t}](/{n})" for n, t in sorted(pagine.items())]
    return "\n".join(righe)


def pagina_supporto(nome_app: str, contatto: str) -> str:
    """The support page, where a person finds how to reach the operator."""
    return "\n".join([
        f"# Supporto — {nome_app}", "",
        "## I comandi che questo bot conosce", "",
        "- `/i-miei-dati` — ti restituisce tutto quello che il bot conserva su di te;",
        "- `/cancellami` — lo cancella.", "",
        "Le risposte sono **private**: le vedi solo tu, anche in un canale pubblico.", "",
        "## Se qualcosa non funziona", "",
        "- **Il comando non compare digitando `/`** — il client non ha aggiornato l'elenco.",
        "  Riavvia Discord.",
        "- **«L'applicazione non ha risposto»** — il bot non ha risposto entro i 3 secondi",
        "  che Discord concede. Riprova; se si ripete, scrivi al contatto qui sotto.", "",
        "## Come si chiede aiuto", "",
        f"Scrivendo a **{contatto}**." if contatto else
        "> ⛔ **DA COMPILARE**: manca un contatto per l'assistenza.", "",
    ])


def termini(modello: str, ordine: dict) -> str:
    """The terms of service template filled with the order data; unknown placeholders stop the build."""
    import string
    t = ordine.get("titolare", {})
    valori = {"bot": ordine["bot"], "contatto": ordine["contatto"], "informativa": ordine["informativa"],
              "titolare_nome": t.get("nome", ""), "titolare_indirizzo": t.get("indirizzo", ""),
              "titolare_email": t.get("email", "")}
    ignoti = sorted({c for _, c, _, _ in string.Formatter().parse(modello) if c and c not in valori})
    if ignoti:
        raise ValueError(f"bot/documenti/termini.md: segnaposto sconosciuti {ignoti} — quelli "
                         f"disponibili sono {sorted(valori)}")
    return modello.format_map(valori)


def genera_pagine(destinazione, nome_app: str, informativa_md: str | None,
                  contatto: str, termini_md: str | None = None) -> list[str]:
    """Write the HTML pages the documents container will serve."""
    from pathlib import Path as _P

    d = _P(destinazione)
    d.mkdir(parents=True, exist_ok=True)
    testi = {"supporto": pagina_supporto(nome_app, contatto)}
    if informativa_md is not None:
        testi["informativa"] = informativa_md
    if termini_md is not None:
        testi["termini"] = termini_md
    testi["index"] = indice(nome_app, {n: t for n, t in PAGINE.items() if n in testi})
    for nome, md in testi.items():
        titolo = PAGINE.get(nome, nome_app)
        (d / f"{nome}.html").write_text(md_a_html(md, titolo), encoding="utf-8")
    return sorted(testi)


def genera_da_albero(albero, ordine: dict, destinazione) -> list[str]:
    """The pages, generated from the handlers' declarations and the order data."""
    from pathlib import Path as _P

    from pythonbots_core.diritti import con_i_diritti
    from pythonbots_core.informativa import genera as _genera_informativa
    from pythonbots_core.instradamento import Registro

    registro = Registro.da_cartella(_P(albero) / "bot" / "handlers")
    accesi = {"informativa": True, "termini": True, **(ordine.get("documenti") or {})}
    informativa_md = _genera_informativa(
        con_i_diritti(registro.dichiarazioni()), ordine["bot"], ordine["contatto"],
        ordine.get("titolare", {})) if accesi["informativa"] else None
    termini_md = None
    if accesi["termini"]:
        modello = _P(albero).joinpath(*MODELLO_TERMINI)
        if not modello.is_file():
            raise FileNotFoundError(
                "manca bot/documenti/termini.md, il modello dei termini di servizio. Se i termini li "
                "pubblichi altrove, scrivi nell'ordine `documenti:` con `termini: false`")
        termini_md = termini(modello.read_text(encoding="utf-8"), ordine)
    return genera_pagine(destinazione, ordine["bot"], informativa_md, ordine["contatto"], termini_md)


def main(argv=None) -> int:
    """Command line entry point for generating the pages from a delivered tree."""
    import sys
    from pathlib import Path as _P

    from pythonbots_core.ordine import carica

    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) != 3:
        sys.exit("uso: python3 -m pythonbots_core.documenti <albero> <ordine.yaml> <destinazione>\n"
                 "  albero       la radice dell'albero consegnato (contiene bot/ e pythonbots_core/)\n"
                 "  ordine.yaml  i dati dell'ordine (vedi pythonbots_core/ordine.py)\n"
                 "  destinazione dove scrivere le pagine .html")
    albero, percorso_ordine, destinazione = a
    ordine = carica(_P(percorso_ordine))
    fatte = genera_da_albero(albero, ordine, destinazione)
    print(f"pagine generate in `{destinazione}`: {', '.join(f'{n}.html' for n in fatte)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
