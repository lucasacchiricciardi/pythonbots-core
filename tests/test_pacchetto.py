"""The package checks itself. Runs against the INSTALLED package (see publish.yml), with no
dependency on the private tooling: what is published must stand on its own."""
from pathlib import Path

import pythonbots_core as p
from pythonbots_core.manifesto import riga_di_avvio, stato


def test_version_is_the_one_declared_in_VERSION():
    s = stato(p.cartella())
    assert p.__version__ == s["versione"] != "sconosciuta"


def test_the_manifest_is_intact():
    """Every file of the installed package matches the sha256 recorded in MANIFEST."""
    assert stato(p.cartella())["manifesto"] == []


def test_the_startup_line_names_both_fingerprints():
    riga = riga_di_avvio(p.cartella())
    assert f"core {p.__version__}" in riga
    assert "manifesto integro" in riga
    assert "impronta " in riga and "wheel " in riga


def test_the_installed_copy_is_not_this_checkout():
    """Guards the smoke job itself: if the checkout shadowed the wheel, the test would prove nothing."""
    assert not Path(p.cartella()).is_relative_to(Path.cwd().parent), p.cartella()
