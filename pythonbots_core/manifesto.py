"""Version and integrity of the core; detected at start-up, never enforced."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ESCLUSI = ("MANIFEST",)


def _impronta(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()


def genera(core: Path) -> dict[str, str]:
    """Relative path to sha256 for every file of the core except the excluded ones."""
    core = Path(core)
    return {
        f.relative_to(core).as_posix(): _impronta(f)
        for f in sorted(core.rglob("*"))
        if f.is_file()
        and "__pycache__" not in f.parts
        and f.relative_to(core).as_posix() not in ESCLUSI
    }


def scrivi(m: dict[str, str]) -> str:
    """The text of the MANIFEST file, one `<sha256>  <path>` per line, sorted."""
    return "".join(f"{i}  {p}\n" for p, i in sorted(m.items()))


def leggi(testo: str) -> dict[str, str]:
    m: dict[str, str] = {}
    for riga in testo.splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#"):
            continue
        impronta, _, percorso = riga.partition("  ")
        if impronta and percorso:
            m[percorso.strip()] = impronta.strip()
    return m


def verifica(core: Path, manifesto: dict[str, str]) -> list[str]:
    """The differences between the core on disk and the manifest; each names the file."""
    attuale = genera(core)
    problemi: list[str] = []
    for percorso in sorted(set(manifesto) | set(attuale)):
        atteso, trovato = manifesto.get(percorso), attuale.get(percorso)
        if atteso is None:
            problemi.append(f"aggiunto: {percorso}")
        elif trovato is None:
            problemi.append(f"mancante: {percorso}")
        elif atteso != trovato:
            problemi.append(f"modificato: {percorso}")
    return problemi


def _campi(testo: str) -> dict[str, str]:
    """`key: value` lines to a dict, with no dependencies."""
    c: dict[str, str] = {}
    for riga in testo.splitlines():
        chiave, sep, valore = riga.partition(":")
        if sep and chiave.strip() and not chiave.strip().startswith("#"):
            c[chiave.strip().lower()] = valore.strip()
    return c


def _leggi_o_vuoto(f: Path) -> str:
    """The file's text, or an empty string when it cannot be read."""
    try:
        return f.read_text(encoding="utf-8")
    except OSError:
        return ""


def impronta(core: Path) -> str:
    """The sha256 of MANIFEST, the figure that identifies the delivered core."""
    m = Path(core) / "MANIFEST"
    return hashlib.sha256(m.read_bytes()).hexdigest() if m.is_file() else "assente"


def wheel_installato(core: Path) -> str:
    """The sha256 of the wheel this copy was installed from, as recorded by pip."""
    dist = sorted(Path(core).parent.glob("pythonbots_core-*.dist-info"))
    if not dist:
        return "non installato"
    try:
        d = json.loads(_leggi_o_vuoto(dist[0] / "direct_url.json") or "{}")
    except ValueError:
        d = {}
    archivio = d.get("archive_info") if isinstance(d, dict) else None
    archivio = archivio if isinstance(archivio, dict) else {}
    h = (archivio.get("hashes") or {}).get("sha256") if isinstance(archivio.get("hashes"), dict) else None
    if not h and isinstance(archivio.get("hash"), str) and archivio["hash"].startswith("sha256="):
        h = archivio["hash"][len("sha256="):]
    return h if isinstance(h, str) and re.fullmatch(r"[0-9a-f]{64}", h) else "senza sha256"


def stato(core: Path, albero: Path | None = None) -> dict[str, object]:
    """What the core says about itself; version, end of life, licence, manifest outcome."""
    core = Path(core)
    v = _campi(_leggi_o_vuoto(core / "VERSION"))
    a = _campi(_leggi_o_vuoto(Path(albero) / "LICENSE-ADDENDUM")) if albero is not None else {}
    testo_manifesto = _leggi_o_vuoto(core / "MANIFEST")
    return {
        "versione": v.get("versione") or "sconosciuta",
        "fine_vita": v.get("fine_vita") or "sconosciuta",
        "rilasciata_il": v.get("rilasciata_il") or "sconosciuta",
        "licenza": a.get("order") or "sconosciuta",
        "manifesto": ("assente" if not testo_manifesto.strip()
                      else verifica(core, leggi(testo_manifesto))),
        "impronta": impronta(core),
        "wheel": wheel_installato(core),
    }


def riga_di_avvio(core: Path, albero: Path | None = None) -> str:
    """The line the core writes to the log at start-up, and that `/about` repeats."""
    s = stato(core, albero)
    m = s["manifesto"]
    esito = ("manifesto assente" if m == "assente"
             else "manifesto integro" if not m
             else f"manifesto NON torna ({len(m)}): " + " · ".join(m))
    return (f"core {s['versione']} · fine vita {s['fine_vita']} · "
            f"licenza {s['licenza']} · {esito} · impronta {s['impronta']} · wheel {s['wheel']}")


def about(core: Path, albero: Path | None = None) -> str:
    """The `/about` text; it is the start-up line, not a copy of it."""
    return riga_di_avvio(core, albero)


def avvia(core: Path, log: list[str], albero: Path | None = None) -> dict[str, object]:
    """The start-up step for integrity; writes the line and always returns."""
    log.append(riga_di_avvio(core, albero))
    return {"avviato": True, "stato": stato(core, albero)}
