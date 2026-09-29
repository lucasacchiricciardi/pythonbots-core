# Changelog

All notable changes to `pythonbots-core` are documented here. The format follows
[Common Changelog](https://common-changelog.org/), and versions follow SemVer.

## [unreleased]

## [0.1.4] - 2026-09-29

### Fixed

- Answer a contended write within Discord's three seconds: the database waits at most 2 seconds for
  a lock (it was 5) and the user gets a private "busy, try again" reply instead of an error.
- Readers no longer wait for writers: the database runs in WAL mode. Back up the whole data folder,
  including `bot.db-wal`.

## [0.1.3] - 2026-09-29

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
