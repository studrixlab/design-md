"""Shared pytest fixtures for the design_md test suite."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
STRIPE_FIXTURE = FIXTURES_DIR / "stripe_DESIGN.md"


@pytest.fixture
def sample_design_md() -> str:
    """Return the raw markdown of the bundled stripe DESIGN.md fixture."""
    return STRIPE_FIXTURE.read_text(encoding="utf-8")


@pytest.fixture
def stripe_fixture_path() -> Path:
    """Return the absolute path to the bundled stripe DESIGN.md fixture."""
    return STRIPE_FIXTURE


@pytest.fixture
def tmp_data_root(tmp_path: Path) -> Path:
    """Build a minimal ``data/`` tree mirroring the upstream submodule layout.

    Layout::

        tmp_path/data/awesome-design-md/design-md/stripe/DESIGN.md

    Returns:
        The ``tmp_path/data`` directory, ready to be passed to ``DataCache``.
    """
    data_root = tmp_path / "data"
    stripe_dir = data_root / "awesome-design-md" / "design-md" / "stripe"
    stripe_dir.mkdir(parents=True)
    shutil.copy(STRIPE_FIXTURE, stripe_dir / "DESIGN.md")
    return data_root
