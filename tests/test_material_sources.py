"""Tests for built-in material sources.

These tests ensure every material in ``MATERIAL_LIBRARY`` specifies a
source URL so that property data can be traced back to its origin.
"""

from __future__ import annotations

from urllib.parse import urlparse

from trussme.components import MATERIAL_LIBRARY


def test_every_material_has_source() -> None:
    """Each material should define a non-empty ``source`` URL."""

    # Act
    sources = [material.get("source", "") for material in MATERIAL_LIBRARY]

    # Assert
    for source in sources:
        parsed = urlparse(source)
        assert parsed.scheme in {"http", "https"}
        assert parsed.netloc


def test_common_materials_present() -> None:
    """Selected materials should ship with the library."""

    # Arrange
    expected = {
        "A36_Steel",
        "A992_Steel",
        "6061_T6_Aluminum",
        "7075_T6_Aluminum",
        "304_Stainless_Steel",
    }

    # Act
    names = {material["name"] for material in MATERIAL_LIBRARY}

    # Assert
    assert expected.issubset(names)
