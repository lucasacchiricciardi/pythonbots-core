# Changelog

All notable changes to `pythonbots-core` are documented here. The format follows
[Common Changelog](https://common-changelog.org/), and versions follow SemVer.

## [unreleased]

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
