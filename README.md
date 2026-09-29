# pythonbots-core

The core library behind PythonBots' Discord bots: an interactions endpoint with Ed25519
signature verification, a handler registry driven by declarations, per-handler data rights
(export and delete), a heartbeat, an integrity manifest, and an `/about` command that reports
what is running.

**Source-available, not open source. Running it requires a licence issued with an order.**
See [`LICENSE`](https://github.com/lucasacchiricciardi/pythonbots-core/blob/main/LICENSE).

## Install

```
pip install pythonbots-core
```

Every order also ships the exact wheel inside its delivery, installed by path so that pip records
the wheel's sha256 next to the package.

## What the package says about itself

At startup, and on `/about`, the core writes one line:

```
core <version> · fine vita <end of life> · licenza <order> · manifesto integro · impronta <sha256 of MANIFEST> · wheel <sha256 of the installed wheel>
```

- `MANIFEST` lists the sha256 of every file in the package; a changed byte is reported with the
  file name. Nothing stops: integrity is detected, never enforced.
- `impronta` is the sha256 of `MANIFEST` itself, the figure recorded in each order's addendum.
- `wheel` is the sha256 pip recorded at install time, comparable with the file on PyPI.

## Releases

Releases are built reproducibly from the tagged source: `SOURCE_DATE_EPOCH` is the release day
declared in `pythonbots_core/VERSION` and setuptools is pinned, so the wheel built from a tag and
the wheel on PyPI have the same sha256. Publishing goes through GitHub Actions with Trusted
Publishing and a reviewed environment.

## Development

This repository receives an export of the package at each release; development happens
elsewhere. Issues are welcome. Code contributions are not accepted — see
[`CONTRIBUTING.md`](https://github.com/lucasacchiricciardi/pythonbots-core/blob/main/CONTRIBUTING.md). Security reports: [`SECURITY.md`](https://github.com/lucasacchiricciardi/pythonbots-core/blob/main/SECURITY.md).
