# Changelog

All notable changes to `pythonbots-core` are documented here. The format follows
[Common Changelog](https://common-changelog.org/), and versions follow SemVer.

## [unreleased]

## [0.1.9] - 2026-10-02

_Upgrade: the wheel only. Optionally, set the image tag in `deploy/compose.yml` to `:0.1.9`, so
that `docker images` tells which core runs._

### Changed

- The licence is version 0.2 (`LICENSE`). It has two layers: anyone with a copy may read and study
  the source and run it for a 30-day evaluation; running it for anything else needs the licence
  issued with an order and recorded in its `LICENSE-ADDENDUM`. Support and the minimum period of
  corrective updates now count from the order's first delivery, so a redelivery no longer extends
  them. The licensor's contact for written notices is in Section 12.
- In a delivery, `deploy/compose.yml` tags the images with the core version it ships
  (`pythonbots/<instance>:0.1.8`), so `docker images` tells which core runs. Until now the tag was
  `0.1.0` whatever the version. The wheel is unchanged.
- The update instructions (delivery README and wiki) end by checking that `/api/battito` answers 200:
  a reverse proxy that resolves container names only when it starts keeps sending `/api` to the old
  container after a rebuild.

## [0.1.8] - 2026-09-30

_Upgrade: besides the wheel, replace `deploy/endpoint.py`, `deploy/lavori.py` and
`deploy/registra_comandi.py` with the new launchers, and **remove** `bot/handlers/diritti.py`: the
rights commands are now in the core, and an old copy stops the bot at start-up, naming the file. The
`diritti.*` texts can be removed from `bot/strings/it.yaml` too (keep them only to reword them). This
is the last release that asks to touch those files: from now on they come with the wheel._

### Changed

- The endpoint, the scheduled jobs and the command registration are in the package
  (`pythonbots_core.servizi`); the files in `deploy/` only start them.
- `/i-miei-dati` and `/cancellami` are core commands, like `/about`, and their texts are core
  strings you can override. A bot with no handlers of its own registers the three core commands.

## [0.1.7] - 2026-09-30

_Upgrade: besides the wheel, replace `deploy/compose.yml` and `deploy/endpoint.py`. Commands are now
registered from the `lavori` container: `docker compose exec lavori python3 deploy/registra_comandi.py`.
With the old `compose.yml` the new endpoint finds the bot token and refuses to start._

### Fixed

- The bot token no longer reaches the internet-facing endpoint: `compose.yml` empties it for the
  `bot` service, the endpoint refuses to start if it finds it, and commands are registered from the
  `lavori` container (`docker compose exec lavori python3 deploy/registra_comandi.py`).
- A signed request counts once: requests whose timestamp is more than five minutes from the bot's
  clock, and interactions already run, are refused with 401.

## [0.1.6] - 2026-09-30

_Upgrade: besides the wheel, replace `deploy/compose.yml`, `deploy/endpoint.py` and
`deploy/registra_comandi.py`, and add `deploy/lavori.py`. `bot/config.yaml` gains a commented
`lavori` example: needed only if a handler declares a `programma`._

### Added

- Scheduled jobs: a handler declares a `programma` (every N minutes, or at HH:MM on chosen days in
  the declared time zone) and a `lavora` function; a separate `lavori` container runs them and posts
  their text to channels named in `bot/config.yaml`. Mentions in job text do not notify anyone.
- `/api/battito` reports the last successful run of each job, and stays `vivo` when the database
  cannot be read.
- Command options: a handler declares `opzioni` per command (text, integer, yes/no, user), reads them
  with `messaggio.opzione(nome)`, and `registra_comandi.py` registers them with Discord. Names, count,
  order and description length are checked before registering.

## [0.1.5] - 2026-09-29

_Upgrade: besides the wheel, replace `deploy/endpoint.py` and `bot/handlers/diritti.py`. In
`bot/strings/it.yaml`, `diritti.copia` now uses `{riassunto}`, and `diritti.copia-link` and
`diritti.copia-troppo-grande` are new; a missing key stops the bot at start-up and names it.
`PB_URL_PUBBLICO` in `deploy/.env` is optional._

### Changed

- `/i-miei-dati` sends a summary in the message and the complete copy as an attached JSON file,
  instead of a list cut at 2000 characters.

### Added

- `risposta.file(chiave, nome, contenuto)` for replies with an attached file, and
  `messaggio.limite_allegati` from Discord's `attachment_size_limit`.
- One-time download links for copies larger than an attachment: `PB_URL_PUBBLICO` sets the base; the
  link expires after 15 minutes and works once. Opening it shows a button, so link previews do not
  use it up.

## [0.1.4] - 2026-09-29

_Upgrade: the wheel only._

### Fixed

- Answer a contended write within Discord's three seconds: the database waits at most 2 seconds for
  a lock (it was 5) and the user gets a private "busy, try again" reply instead of an error.
- Readers no longer wait for writers: the database runs in WAL mode. Back up the whole data folder,
  including `bot.db-wal`.

## [0.1.3] - 2026-09-29

_Upgrade: besides the wheel, replace `deploy/endpoint.py` and `bot/handlers/diritti.py`. In
`bot/strings/it.yaml` the `diritti.*` texts change and `diritti.nulla-da-cancellare` is new._

### Added

- Handlers can store data: `gestisci(messaggio, risposta, dati)` receives access to the handler's own
  tables, with Discord identifiers pseudonymised on write and in filters. Two-parameter handlers are
  unchanged.
- `/i-miei-dati` shows and `/cancellami` deletes the data every handler keeps on the person asking.
- Reply texts take values: `risposta.testo(chiave, quanti=3)` fills `{quanti}`.
- The fake adapters accept a `deposito`, and use an in-memory database without one.

### Fixed

- Apply the core's database migrations from the installed package: a delivered project has no
  `pythonbots_core/` folder, and the core tables were silently not created.
- The delivered rights texts no longer contain one bot's privacy notice URL.

## [0.1.2] - 2026-09-29

### Added

- Terms of service page (`/termini`), filled from a template the client owns in
  `bot/documenti/termini.md` and ships as a draft to be reviewed by a lawyer.
- Order section `documenti` to switch the privacy notice and the terms page on or off.

## [0.1.1] - 2026-09-29

### Fixed

- Publish the project description on PyPI: 0.1.0 shipped without one, and a published release
  cannot be amended.

## [0.1.0] - 2026-09-28

_First public release._

### Added

- Discord interactions endpoint with Ed25519 signature verification and a 3-second reply budget.
- Handler registry built from each handler's declaration: triggers, string keys, declared data.
- Per-handler data rights: export and delete, driven by the same declarations.
- Heartbeat file and endpoint (`/api/battito`) reporting received, succeeded and failed interactions.
- Integrity manifest (`MANIFEST`, sha256 per file) and version metadata (`VERSION`), reported at
  startup and on `/about` together with the manifest fingerprint and the sha256 of the installed wheel.
- Pseudonymised user identifiers in the data store, keyed by a secret the deployment provides.
- Privacy notice and support pages generated from the handlers' declarations and the order data.
