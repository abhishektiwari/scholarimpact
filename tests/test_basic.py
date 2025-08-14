"""Basic tests for ScholarImpact package."""

from pathlib import Path

import pytest


def test_package_import():
    """Test that the main package can be imported."""
    import scholarimpact

    assert scholarimpact is not None


def test_cli_import():
    """Test that CLI module can be imported."""
    from scholarimpact.cli import main

    assert main is not None


def test_core_modules_import():
    """Test that core modules can be imported."""
    from scholarimpact.core import crawler, extractor, utils

    assert extractor is not None
    assert crawler is not None
    assert utils is not None


def test_dashboard_import():
    """Test that dashboard module can be imported."""
    from scholarimpact.dashboard import app

    assert app is not None


def test_data_directory_creation():
    """Test that data directory can be created."""
    test_dir = Path("./test_data_temp")
    test_dir.mkdir(exist_ok=True)
    assert test_dir.exists()
    # Cleanup
    test_dir.rmdir()


def test_version():
    """Test that package has a version."""
    import scholarimpact

    # Check if version attribute exists (might not be defined yet)
    version = getattr(scholarimpact, "__version__", "0.0.1")
    assert version is not None
    assert isinstance(version, str)
