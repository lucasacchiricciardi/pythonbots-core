"""The core's message model; a handler never sees a platform object."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Messaggio:
    """What arrives; immutable."""
    testo: str = ""
    comando: str = ""
    mittente: str = ""
    conversazione: str = ""
    allegati: tuple = ()
    limite_allegati: int = 0
    opzioni: tuple = ()

    def opzione(self, nome: str, predefinito=None):
        """The value of option `nome`, or the default when the user did not give it."""
        return dict(self.opzioni).get(nome, predefinito)


@dataclass(frozen=True)
class Azione:
    """What a handler asked for; an intention, not a sent message."""
    chiave: str
    privata: bool = False
    opzioni: tuple = ()
    testo_degradato: str = ""
    testo: str = ""
    valori: tuple = ()
    allegato: tuple = ()


class Risposta:
    """The handler's notepad; it records what to say, not how to send it."""

    def __init__(self) -> None:
        self._azioni: list[Azione] = []

    def testo(self, chiave: str, **valori) -> None:
        self._azioni.append(Azione(chiave, valori=tuple(sorted(valori.items()))))

    def privata(self, chiave: str, **valori) -> None:
        """Reply privately; the form for anything that concerns one person's data."""
        self._azioni.append(Azione(chiave, privata=True, valori=tuple(sorted(valori.items()))))

    def pulsanti(self, chiave: str, opzioni, **valori) -> None:
        self._azioni.append(Azione(chiave, opzioni=tuple(opzioni), valori=tuple(sorted(valori.items()))))

    def file(self, chiave: str, nome: str, contenuto: bytes, privata: bool = True, **valori) -> None:
        """A message with an attached file; private by default."""
        self._azioni.append(Azione(chiave, privata=privata, valori=tuple(sorted(valori.items())),
                                   allegato=(nome, bytes(contenuto))))

    def fatto(self, chiave: str, testo: str, privata: bool = True) -> None:
        """A fact rather than a phrase; the text is computed, not translated."""
        self._azioni.append(Azione(chiave, privata=privata, testo=testo))

    @property
    def azioni(self) -> tuple[Azione, ...]:
        return tuple(self._azioni)
