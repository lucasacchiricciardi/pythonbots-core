# Security

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting on this repository:
**Security → Report a vulnerability**. You will get an acknowledgement, and a fix arrives as a
release of the package.

## Supported versions

The latest release. Clients receive corrective updates on the terms of their order.

## What the package does and does not do

- The Discord interactions endpoint verifies the Ed25519 signature over timestamp and body on
  every request and rejects anything unsigned or altered. It also rejects a request whose signed
  timestamp is more than five minutes away from the bot's clock, and an interaction it has already
  run: a captured request repeated unchanged is refused.
- The package never reads a secret with a default value: a missing environment variable stops
  the process at startup and says which one.
- Integrity is detected, not enforced: a modified installation keeps running and reports the
  modified files at startup and on `/about`.
