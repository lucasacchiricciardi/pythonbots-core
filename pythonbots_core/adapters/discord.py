"""The Discord adapter for the Interactions Endpoint (called form)."""
from __future__ import annotations

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from pythonbots_core.adapters import Capacita, instrada
from pythonbots_core.messaggio import Messaggio

PING = 1
COMANDO = 2

PONG = {"type": PING}

RISPOSTA_MESSAGGIO = 4

EFFIMERO = 64

CHIAVE_NON_MIO = "core.comando-sconosciuto"

FILE = "_file"


def corpo_http(risposta: dict) -> tuple[bytes, str]:
    """The response as an HTTP body; JSON without files, multipart/form-data with them."""
    import json
    import uuid
    file = risposta.get(FILE) or []
    carico = {k: v for k, v in risposta.items() if k != FILE}
    if not file:
        return json.dumps(carico).encode(), "application/json"
    confine = uuid.uuid4().hex
    parti = [f'--{confine}\r\nContent-Disposition: form-data; name="payload_json"\r\n'
             f'Content-Type: application/json\r\n\r\n'.encode() + json.dumps(carico).encode() + b"\r\n"]
    for n, (nome, contenuto) in enumerate(file):
        parti.append(f'--{confine}\r\nContent-Disposition: form-data; name="files[{n}]"; filename="{nome}"'
                     f'\r\nContent-Type: application/json\r\n\r\n'.encode() + contenuto + b"\r\n")
    parti.append(f"--{confine}--\r\n".encode())
    return b"".join(parti), f"multipart/form-data; boundary={confine}"


class FirmaNonValida(Exception):
    """The request was not signed by Discord, or not as Discord signed it."""


class Discord:
    """Verify, translate, route, translate back; decides nothing on its own."""

    capacita = Capacita(pulsanti=True, privato=True)

    def __init__(self, chiave_pubblica: str) -> None:
        self._verifica = VerifyKey(bytes.fromhex(chiave_pubblica))

    def _controlla_firma(self, corpo: bytes, testate) -> None:
        firma = testate.get("X-Signature-Ed25519")
        timestamp = testate.get("X-Signature-Timestamp")
        if not firma or not timestamp:
            raise FirmaNonValida("testate di firma mancanti")
        try:
            self._verifica.verify(timestamp.encode() + corpo, bytes.fromhex(firma))
        except (BadSignatureError, ValueError) as e:
            raise FirmaNonValida("firma non valida") from e

    def ricevi(self, registro, corpo: bytes, testate, stringhe, battito=None, deposito=None) -> dict:
        """One Discord request to the response to return; raises when it is not Discord's."""
        self._controlla_firma(corpo, testate)

        import json
        evento = json.loads(corpo)
        if evento.get("type") == PING:
            return PONG

        messaggio = self._traduci(evento)
        azioni = instrada(registro, messaggio, self.capacita, stringhe, battito, deposito)
        if not azioni:
            return self._risposta(stringhe.testo(CHIAVE_NON_MIO), privata=True)

        prima = azioni[0]
        return self._risposta(prima.testo, privata=prima.privata, allegato=prima.allegato)

    @staticmethod
    def _traduci(evento: dict) -> Messaggio:
        """A Discord event to the core message model."""
        utente = (evento.get("member") or {}).get("user") or evento.get("user") or {}
        nome = (evento.get("data") or {}).get("name", "")
        return Messaggio(
            testo=nome,
            comando=f"/{nome}" if nome else "",
            mittente=str(utente.get("id", "")),
            conversazione=str(evento.get("channel_id", "")),
            limite_allegati=int(evento.get("attachment_size_limit") or 0),
            opzioni=tuple(sorted((o["name"], o.get("value")) for o in
                                 (evento.get("data") or {}).get("options") or [] if "name" in o)),
        )

    @staticmethod
    def _risposta(testo: str, privata: bool, allegato: tuple = ()) -> dict:
        dati = {"content": testo}
        if privata:
            dati["flags"] = EFFIMERO
        risposta = {"type": RISPOSTA_MESSAGGIO, "data": dati}
        if allegato:
            dati["attachments"] = [{"id": 0, "filename": allegato[0]}]
            risposta[FILE] = [allegato]
        return risposta
