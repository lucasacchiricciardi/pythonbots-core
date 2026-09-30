"""User-facing strings, kept out of the code, per language."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

FORMA_CHIAVE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.[a-z0-9]+(?:-[a-z0-9]+)*$")


class ChiaveMancante(KeyError):
    """A key used and not translated."""


class Stringhe:
    """Key to text, for one language."""

    def __init__(self, voci: dict[str, str], lingua: str = "it") -> None:
        self._voci = dict(voci)
        self.lingua = lingua

    def __contains__(self, chiave: str) -> bool:
        return chiave in self._voci

    def testo(self, chiave: str) -> str:
        if chiave not in self._voci:
            raise ChiaveMancante(
                f"la chiave `{chiave}` non e' tradotta in `{self.lingua}`. "
                f"Si aggiunge in `bot/strings/{self.lingua}.yaml`: il core non ripiega "
                f"sulla chiave, perche' mostrarla e' il difetto che questo file rimuove.")
        return self._voci[chiave]

    def chiavi(self) -> frozenset[str]:
        return frozenset(self._voci)

    def mancanti(self, dichiarate) -> list[str]:
        """Which declared keys have no text; called at start-up."""
        return sorted(k for k in dichiarate if k not in self._voci)


CARTELLA_CORE = Path(__file__).resolve().parent / "strings"


def _leggi(p: Path, vuoto_ammesso: bool = False) -> dict:
    """One file to a dict, with an error that says what is wrong for each way to fail."""
    if not p.is_file():
        raise FileNotFoundError(
            f"manca il file delle stringhe `{p}`. Non c'e' un default: un bot senza le "
            f"sue frasi non e' un bot che parla inglese, e' un bot rotto.")

    caricato = yaml.safe_load(p.read_text(encoding="utf-8"))
    if caricato is None and vuoto_ammesso:
        return {}
    if caricato is None:
        raise ValueError(f"`{p}` e' vuoto: nessuna stringa da usare.")
    if not isinstance(caricato, dict):
        raise ValueError(f"`{p}` deve essere una mappa `chiave: testo`, "
                         f"non {type(caricato).__name__}.")

    storte = sorted(k for k in caricato if not FORMA_CHIAVE.match(str(k)))
    if storte:
        raise ValueError(
            f"in `{p}` queste chiavi non hanno la forma `gruppo.nome` "
            f"(minuscole, trattini ammessi): {storte}")

    non_testo = sorted(k for k, v in caricato.items() if not isinstance(v, str))
    if non_testo:
        raise ValueError(f"in `{p}` queste voci non sono testo: {non_testo}")

    vuote = sorted(k for k, v in caricato.items() if not v.strip())
    if vuote:
        raise ValueError(
            f"in `{p}` queste voci sono vuote: {vuote}. Una stringa vuota manda un "
            f"messaggio senza contenuto, che Discord rifiuta con 400 — e il cliente "
            f"vedrebbe un guasto del bot invece di una riga da riempire.")
    return caricato


def carica(cartella_bot, lingua: str = "it") -> Stringhe:
    """The core's phrases plus the bot's, with the latter taking precedence."""
    voci = _leggi(CARTELLA_CORE / f"{lingua}.yaml")
    cartella = Path(cartella_bot)
    voci.update(_leggi(cartella / f"{lingua}.yaml" if cartella.is_dir() else cartella, vuoto_ammesso=True))
    return Stringhe(voci, lingua)
