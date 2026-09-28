"""In-memory fake adapters for tests."""
from __future__ import annotations

from pythonbots_core.adapters import Capacita, instrada
from pythonbots_core.messaggio import Azione, Messaggio


class FintoChiamato:
    """The called adapter; the platform delivers an event and it answers."""

    def __init__(self, capacita: Capacita | None = None) -> None:
        self.capacita = capacita or Capacita()

    def ricevi(self, registro, messaggio: Messaggio, stringhe) -> list[Azione]:
        return instrada(registro, messaggio, self.capacita, stringhe)


class FintoCicloProprio:
    """The adapter that owns the loop; it has a queue and consumes it."""

    def __init__(self, capacita: Capacita | None = None, eventi=()) -> None:
        self.capacita = capacita or Capacita()
        self.eventi = list(eventi)

    def gira(self, registro, stringhe) -> list[Azione]:
        """Consume every event; return what was emitted, in order."""
        uscita: list[Azione] = []
        for m in self.eventi:
            uscita += instrada(registro, m, self.capacita, stringhe)
        return uscita
