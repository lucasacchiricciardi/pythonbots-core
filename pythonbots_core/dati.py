"""What a handler sees of the database; its own tables only, identifiers pseudonymised."""
from __future__ import annotations

import os
import re

from pythonbots_core import copie
from pythonbots_core.deposito import Deposito, campi_da_api
from pythonbots_core.diritti import cancella as _cancella_persona
from pythonbots_core.diritti import PERSONA, _campi, esporta, possiede
from pythonbots_core.riservatezza import pseudonimo

_NOME = re.compile(r"^[a-z][a-z0-9_]*$")


class Dati:
    """One handler's access to the store, restricted to its tables."""

    def __init__(self, deposito: Deposito, dichiarazione: dict, dichiarazioni: list[dict],
                 persona: str = "") -> None:
        self._d = deposito
        self._dich = dichiarazione
        self._tutte = dichiarazioni
        self._persona = persona

    def _chi(self) -> str:
        if not self._persona:
            raise RuntimeError("miei_dati/cancella_i_miei valgono per chi ha mandato il comando, "
                               "e questo accesso non ha una persona")
        return pseudonimo(self._persona)

    def _nessuno_conserva_persone(self) -> bool:
        return not any(PERSONA in _campi(d) for d in self._tutte)

    def miei_dati(self) -> dict[str, list[dict]]:
        """Everything the bot keeps on the person who sent the command, by table."""
        chi = self._chi() if not self._nessuno_conserva_persone() else None
        return esporta(self._d, self._tutte, chi) if chi else {}

    def cancella_i_miei(self) -> dict[str, int]:
        """Delete what the bot keeps on the person who sent the command; rows removed, by table."""
        chi = self._chi() if not self._nessuno_conserva_persone() else None
        if not chi:
            return {}
        tolte = _cancella_persona(self._d, self._tutte, chi)
        copie.cancella_persona(self._d, chi)
        return tolte

    def link_mia_copia(self) -> str | None:
        """A one-time link to download one's own copy, or None if the bot does not know its address."""
        base = os.environ.get("PB_URL_PUBBLICO", "").rstrip("/")
        if not base:
            return None
        return f"{base}/api/copia/{copie.crea(self._d, self._chi())}"

    def _tabella(self, tabella: str) -> set[str]:
        if not isinstance(tabella, str) or not _NOME.match(tabella):
            raise ValueError(f"nome di tabella non valido: {tabella!r} (minuscole, cifre, _)")
        if not possiede(self._dich, tabella):
            raise PermissionError(f"la tabella `{tabella}` non e' dell'handler `{self._dich['nome']}`: "
                                  f"puo' usare solo `{self._dich['nome']}` e `{self._dich['nome']}_…`")
        return campi_da_api(self._tutte, tabella) or set()

    def _filtro(self, da_api: set[str], filtri: dict) -> tuple[str, tuple]:
        for c in filtri:
            if not _NOME.match(c):
                raise ValueError(f"nome di colonna non valido: {c!r}")
        if not filtri:
            return "", ()
        return (" WHERE " + " AND ".join(f"{c} = ?" for c in filtri),
                tuple(pseudonimo(v) if c in da_api else v for c, v in filtri.items()))

    def scrivi(self, tabella: str, **valori) -> None:
        self._tabella(tabella)
        for c in valori:
            if not _NOME.match(c):
                raise ValueError(f"nome di colonna non valido: {c!r}")
        self._d.scrivi(tabella, self._tutte, **valori)
        self._d.conferma()

    def righe(self, tabella: str, **filtri) -> list[dict]:
        da_api = self._tabella(tabella)
        dove, parametri = self._filtro(da_api, filtri)
        cur = self._d._c.execute(f"SELECT * FROM {tabella}{dove}", parametri)
        colonne = [c[0] for c in cur.description]
        return [dict(zip(colonne, r)) for r in cur.fetchall()]

    def aggiorna(self, tabella: str, dove: dict, **valori) -> int:
        da_api = self._tabella(tabella)
        if not dove or not valori:
            raise ValueError("aggiorna vuole almeno un filtro (dove) e un valore")
        filtro, parametri = self._filtro(da_api, dove)
        for c in valori:
            if not _NOME.match(c):
                raise ValueError(f"nome di colonna non valido: {c!r}")
        imposta = ", ".join(f"{c} = ?" for c in valori)
        nuovi = tuple(pseudonimo(v) if c in da_api else v for c, v in valori.items())
        n = self._d._c.execute(f"UPDATE {tabella} SET {imposta}{filtro}", nuovi + parametri).rowcount
        self._d.conferma()
        return n

    def cancella(self, tabella: str, **filtri) -> int:
        da_api = self._tabella(tabella)
        if not filtri:
            raise ValueError("cancella vuole almeno un filtro: svuotare la tabella per sbaglio non si puo'")
        dove, parametri = self._filtro(da_api, filtri)
        n = self._d._c.execute(f"DELETE FROM {tabella}{dove}", parametri).rowcount
        self._d.conferma()
        return n
