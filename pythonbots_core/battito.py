"""The heartbeat, which says "it did its job" rather than "the process responds"."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

NOME_FILE = "battito.json"

VUOTO = {"ultimo_lavoro_riuscito": None, "ricevuti": 0, "riusciti": 0}


def _adesso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class Battito:
    """Heartbeat state on a file; two writes per interaction, nothing kept in memory."""

    def __init__(self, percorso: Path) -> None:
        self.percorso = Path(percorso)


    def _leggi(self) -> dict:
        """The state on disk, or the empty one."""
        try:
            d = json.loads(self.percorso.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return dict(VUOTO)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"battito: stato illeggibile ({type(e).__name__}), riparto da vuoto: "
                  f"{self.percorso}", file=sys.stderr, flush=True)
            return dict(VUOTO)
        if not isinstance(d, dict):
            return dict(VUOTO)
        s = dict(VUOTO)
        t = d.get("ultimo_lavoro_riuscito")
        if isinstance(t, str):
            s["ultimo_lavoro_riuscito"] = t
        for k in ("ricevuti", "riusciti"):
            v = d.get(k)
            if isinstance(v, int) and not isinstance(v, bool) and v >= 0:
                s[k] = v
        return s

    def _scrivi(self, s: dict) -> None:
        """Atomic write; a failure is reported rather than lost."""
        tmp = self.percorso.with_suffix(self.percorso.suffix + f".{os.getpid()}.tmp")
        try:
            tmp.write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.percorso)
        except OSError as e:
            print(f"battito: scrittura FALLITA ({type(e).__name__}: {e}) su "
                  f"{self.percorso} — il battito restera' indietro", file=sys.stderr,
                  flush=True)
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass


    def ricevuto(self) -> None:
        """A handler has been invoked; recorded before calling it."""
        s = self._leggi()
        s["ricevuti"] += 1
        self._scrivi(s)

    def riuscito(self) -> None:
        """A job finished without error; advances the timestamp and the success count."""
        s = self._leggi()
        s["riusciti"] += 1
        s["ultimo_lavoro_riuscito"] = _adesso()
        self._scrivi(s)


    def stato(self) -> dict:
        """The three counters plus the two derived figures."""
        s = self._leggi()
        t = s["ultimo_lavoro_riuscito"]
        eta = None
        if t:
            try:
                q = datetime.fromisoformat(t.replace("Z", "+00:00"))
                eta = max(0, int((datetime.now(timezone.utc) - q).total_seconds()))
            except ValueError:
                eta = None
        return {**s, "falliti": s["ricevuti"] - s["riusciti"], "eta_secondi": eta}
