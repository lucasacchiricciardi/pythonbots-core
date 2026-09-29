"""Who answers what; the core piece between the adapter and the handlers."""
from __future__ import annotations

import importlib.util
from pathlib import Path


class Registro:
    """Trigger to function, and nothing else."""

    def __init__(self) -> None:
        self._per_trigger: dict[str, tuple[str, object]] = {}
        self._chiavi: set[str] = set()
        self._dichiarazioni: list[dict] = []

    def aggiungi(self, nome: str, trigger, gestisci, chiavi_stringhe=(),
                 dichiarazione=None) -> None:
        for t in trigger:
            self._per_trigger[t] = (nome, gestisci)
        self._chiavi.update(chiavi_stringhe)
        if dichiarazione is not None:
            self._dichiarazioni.append(dichiarazione)

    def dichiarazioni(self) -> list[dict]:
        """The whole declarations of the loaded handlers, in loading order."""
        return self._dichiarazioni

    def comandi(self) -> list[tuple[str, str]]:
        """(trigger, handler name) for every routed command, in order."""
        return sorted((t, nome) for t, (nome, _) in self._per_trigger.items())

    def chiavi_stringhe(self) -> frozenset[str]:
        """The string keys declared by the loaded handlers."""
        return frozenset(self._chiavi)

    def dichiarazione(self, comando: str) -> dict | None:
        """The declaration of the handler for this command, or None."""
        voce = self._per_trigger.get(comando)
        if voce is None:
            return None
        return next((d for d in self._dichiarazioni if d.get("nome") == voce[0]), None)

    def cerca(self, comando: str):
        """The handler for this command, or None."""
        voce = self._per_trigger.get(comando)
        return voce[1] if voce else None

    @classmethod
    def da_albero(cls, albero: Path) -> Registro:
        """The client's handlers plus the core's commands."""
        from pythonbots_core import cartella
        from pythonbots_core.about import registra
        albero = Path(albero)
        r = cls.da_cartella(albero / "bot" / "handlers")
        registra(r, cartella(), albero)
        return r

    @classmethod
    def da_cartella(cls, handlers: Path) -> Registro:
        """Load the delivered handlers by reading their declarations."""
        r = cls()
        for f in sorted(Path(handlers).glob("*.py")):
            if f.stem.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(f"handler_{f.stem}", f)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            d = getattr(modulo, "DICHIARAZIONE", None)
            gestisci = getattr(modulo, "gestisci", None)
            if not d or not callable(gestisci):
                continue
            r.aggiungi(d["nome"], d.get("trigger", ()), gestisci,
                       d.get("chiavi_stringhe", ()), d)
        return r
