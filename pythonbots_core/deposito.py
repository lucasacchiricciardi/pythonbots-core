"""The boundary between the core and the database; a single class crosses it."""
from __future__ import annotations

import sqlite3
from pathlib import Path


REGISTRO_CORE = "core_migrazioni"
REGISTRO_BOT = "migrazioni"
REGISTRI = (REGISTRO_CORE, REGISTRO_BOT)


def campi_da_api(dichiarazioni, tabella: str) -> set[str] | None:
    """The columns of the table that come from Discord, or None when no handler declares it."""
    for d in dichiarazioni:
        nome = d.get("nome", "")
        if tabella == nome or tabella.startswith(nome + "_"):
            return {v["campo"] for v in d.get("dati_memorizzati", ()) if v.get("da_api")}
    return None


class Deposito:
    """Opens the database with the declared dialect. Nothing else."""

    dialetto = "sqlite"

    def __init__(self, percorso: Path):
        self.percorso = percorso
        self._c = sqlite3.connect(percorso)
        self._c.execute("PRAGMA foreign_keys = ON")

    def esegui(self, sql: str, parametri: tuple = ()) -> None:
        self._c.execute(sql, parametri)

    def esegui_copione(self, sql: str) -> None:
        """Several statements at once, as a migration needs."""
        self._c.executescript(sql)

    def leggi(self, sql: str, parametri: tuple = ()) -> list[tuple]:
        return self._c.execute(sql, parametri).fetchall()

    def tabelle(self) -> set[str]:
        return {r[0] for r in self.leggi(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}

    def colonne(self, tabella: str) -> set[str]:
        return {r[1] for r in self.leggi(f"PRAGMA table_info({tabella})")}

    def scrivi(self, tabella: str, dichiarazioni, **valori) -> None:
        """Insert one row, pseudonymising what is declared as coming from the API."""
        from pythonbots_core.riservatezza import pseudonimo

        da_api = campi_da_api(dichiarazioni, tabella)
        if da_api is None:
            raise ValueError(
                f"tabella `{tabella}` non dichiarata da nessun handler: non so quali "
                f"colonne vengano da Discord, e non scrivo API Data in chiaro (§ 5(c))")

        colonne = list(valori)
        segnaposto = ", ".join("?" for _ in colonne)
        dati = tuple(pseudonimo(valori[c]) if c in da_api else valori[c] for c in colonne)
        self.esegui(f"INSERT INTO {tabella} ({', '.join(colonne)}) VALUES ({segnaposto})",
                    dati)

    def conferma(self) -> None:
        self._c.commit()

    def chiudi(self) -> None:
        self._c.close()

    def __enter__(self): return self
    def __exit__(self, *_): self.conferma(); self.chiudi()


def applica_catena(deposito: Deposito, cartella: Path, registro: str) -> list[str]:
    """Apply, in order, the migrations not yet applied, and record them."""
    deposito.esegui_copione(
        f"CREATE TABLE IF NOT EXISTS {registro} ("
        " numero VARCHAR(8) NOT NULL,"
        " nome VARCHAR(255) NOT NULL,"
        " PRIMARY KEY (numero));")
    gia = {r[0] for r in deposito.leggi(f"SELECT numero FROM {registro}")}

    applicate: list[str] = []
    for f in sorted(cartella.glob("*.sql")):
        numero = f.name.split("_", 1)[0]
        if numero in gia:
            continue
        deposito.esegui_copione(f.read_text(encoding="utf-8"))
        deposito.esegui(f"INSERT INTO {registro} (numero, nome) VALUES (?, ?)",
                        (numero, f.name))
        applicate.append(f.name)
    deposito.conferma()
    return applicate


def avvia(albero: Path, db: Path, core: Path | None = None) -> dict:
    """Bot start-up; the core's migration chain first, then the client's."""
    if core is None:
        from pythonbots_core import cartella
        core = cartella() / "migrations"
    ordine: list[str] = []
    with Deposito(db) as d:
        core = applica_catena(d, core, REGISTRO_CORE)
        ordine.append("core")
        bot = applica_catena(d, albero / "bot" / "migrations", REGISTRO_BOT)
        ordine.append("bot")
        return {"core": core, "bot": bot, "ordine": ordine, "tabelle": d.tabelle()}
