"""The application's privacy notice, generated from the handlers' declarations."""
from __future__ import annotations

NIENTE = "**Questo bot non conserva nessun dato su di te.**"

CAMPI_TITOLARE = ("nome", "indirizzo", "email")


def problemi_titolare(titolare: dict) -> list[str]:
    """The missing fields of the data controller, as a list."""
    return [f"titolare: manca `{c}`" for c in CAMPI_TITOLARE
            if not str(titolare.get(c, "")).strip()]


def _tabella_dati(voci) -> list[str]:
    righe = ["| dato | cosa contiene | per quanto si conserva | viene da Discord |",
             "|---|---|---|---|"]
    for nome, v in voci:
        da = "sì" if v.get("da_api") else "no"
        righe.append(f"| `{nome}.{v['campo']}` | {v['contiene']} | {v['conservato']} "
                     f"| {da} |")
    return righe


def genera(dichiarazioni: list[dict], nome_app: str, contatto: str,
           titolare: dict | None = None) -> str:
    """The privacy notice; it is regenerated, never written by hand."""
    titolare = titolare or {}
    voci = [(d["nome"], v) for d in sorted(dichiarazioni, key=lambda x: x["nome"])
            for v in d.get("dati_memorizzati", ())]
    da_discord = any(v.get("da_api") for _, v in voci)

    r = [f"# Informativa privacy — {nome_app}", "",
         "Questo documento riguarda **l'applicazione Discord**, non un sito web: descrive",
         "cosa il bot conserva su di te, per quanto, e come chiederne una copia o la",
         "cancellazione.", "",
         "Le sezioni sui dati sono **generate dalle dichiarazioni degli handler**: dicono",
         "quello che il bot fa davvero, non quello che qualcuno si è ricordato di scrivere.",
         "", "---", "",
         "## Titolare del trattamento", ""]

    if problemi_titolare(titolare):
        r += ["> ⛔ **DA COMPILARE.** Questa informativa non è pubblicabile finché il",
              "> titolare del trattamento non è indicato: senza, non si sa a chi scrivere",
              "> per esercitare un diritto.", ""]
    else:
        r += [f"**{titolare['nome']}**  ", f"{titolare['indirizzo']}  "]
        if titolare.get("piva"):
            r.append(f"P.IVA {titolare['piva']}  ")
        r += [f"Email: **{titolare['email']}**", ""]

    r += ["---", "", "## Cosa raccoglie, e per quanto", ""]
    r += [NIENTE, ""] if not voci else _tabella_dati(voci) + [""]

    if da_discord:
        r += ["I dati che **vengono da Discord** — cioè gli identificativi con cui il bot",
              "ritrova le tue righe — non sono conservati in chiaro: al loro posto viene",
              "scritto uno **pseudonimo irreversibile**, che non permette di risalire",
              "all'identificativo originale. Serve solo a ritrovare i tuoi dati quando sei",
              "**tu** a chiederli.", ""]

    r += ["---", "", "## ⛔ Cosa questo bot NON fa", "",
          "Dichiarare le assenze è parte dell'informativa, non una cortesia: un documento",
          "che elenca solo le presenze lascia a chi legge il dubbio su tutto il resto.", "",
          "- **Non usa cookie né altri strumenti di tracciamento.** Non è un sito web.",
          "- **Non raccoglie il tuo indirizzo IP.** Il server non lo registra.",
          "- **Non legge i messaggi del server.** Non ha l'intent `MESSAGE_CONTENT`, e",
          "  senza quello Discord non glieli manda affatto.",
          "- **Non profila e non fa pubblicità.** Non esistono decisioni automatizzate che",
          "  ti riguardino.",
          "- **Non vende né condivide** i tuoi dati con terzi.", "",
          "---", "", "## Perché li conserva, e su quale base",
          "",
          "Per **fornire il servizio che hai chiesto** usando i comandi del bot",
          "(art. 6(1)(b) GDPR — esecuzione di un contratto o di misure precontrattuali),",
          "e per gli obblighi di legge a cui il titolare è soggetto (art. 6(1)(c)).", "",
          ("Al termine del periodo indicato nella tabella i dati sono cancellati."
           if voci else
           "Non essendoci dati conservati, non c'è nessun periodo di conservazione."), "",
          "---", "", "## I tuoi diritti, e come esercitarli", "",
          "Puoi chiedere: **accesso** ai tuoi dati, **rettifica**, **cancellazione**,",
          "**limitazione** del trattamento, **portabilità**, e **opposizione** al",
          "trattamento. Puoi inoltre proporre **reclamo** al Garante per la protezione dei",
          "dati personali.", "",
          "⭐ Per i due più frequenti non serve scrivere a nessuno — sono comandi del bot,",
          "e la risposta la vedi solo tu:", "",
          "- `/i-miei-dati` — ti restituisce tutto quello che il bot conserva su di te;",
          "- `/cancellami` — lo cancella.", ""]

    if contatto:
        r += [f"Per tutto il resto: **{contatto}**.", ""]
    else:
        r += ["> ⛔ **DA COMPILARE**: manca un contatto. I comandi non bastano — se il bot",
              "> è fermo, una persona deve poter scrivere a qualcuno.", ""]

    r += ["---", "", "## Modifiche", "",
          "Questa informativa può cambiare quando cambia il bot. Essendo **generata dalle",
          "dichiarazioni degli handler**, cambia *insieme* al codice e non dopo: è la",
          ("ragione per cui la tabella qui sopra si può leggere come vera."
           if voci else
           "ragione per cui l'assenza dichiarata qui sopra si può leggere come vera."), ""]
    return "\n".join(r)


def problemi(testo: str, dichiarazioni: list[dict]) -> list[str]:
    """The gap between the published notice and what the bot declares it does."""
    attesi = [f"{d['nome']}.{v['campo']}"
              for d in dichiarazioni for v in d.get("dati_memorizzati", ())]
    p = [f"informativa: manca il dato `{a}`, che `{a.split('.')[0]}` dichiara di conservare"
         for a in attesi if a not in testo]
    if attesi and NIENTE in testo:
        p.append("informativa: dice che non si conserva niente, ma gli handler dichiarano "
                 f"{len(attesi)} dati")
    if "DA COMPILARE" in testo:
        p.append("informativa: contiene un segnaposto `DA COMPILARE` — non è pubblicabile")
    return p
