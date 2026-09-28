"""Smoke tests for the skeleton."""

from __future__ import annotations


def test_version_exposed():
    import stampkit

    assert stampkit.__version__


def test_cli_importable():
    from stampkit.cli.main import app

    assert app is not None


def test_report_schema_version():
    from stampkit.report.schema import SCHEMA_VERSION

    assert SCHEMA_VERSION == "1.0"
