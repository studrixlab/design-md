"""Tests for design_md.parser.DesignMdParser."""

from __future__ import annotations

from design_md.parser import CANONICAL_SECTIONS, DesignMdParser


def test_parse_returns_all_sections(sample_design_md: str) -> None:
    parser = DesignMdParser()
    result = parser.parse(sample_design_md)
    sections = result["sections"]
    assert len(sections) == 9
    for canonical in CANONICAL_SECTIONS:
        assert canonical in sections, f"missing section: {canonical}"


def test_parse_returns_raw(sample_design_md: str) -> None:
    parser = DesignMdParser()
    result = parser.parse(sample_design_md)
    assert result["raw"] == sample_design_md


def test_extract_colors_basic(sample_design_md: str) -> None:
    parser = DesignMdParser()
    colors = parser.parse(sample_design_md)["colors"]
    assert len(colors) >= 3
    hexes = {c["hex"] for c in colors}
    assert "#533afd" in hexes
    assert "#061b31" in hexes
    for color in colors:
        assert color["hex"].startswith("#")
        assert color["name"]
        assert color["description"]


def test_extract_colors_handles_no_colors() -> None:
    parser = DesignMdParser()
    md = "## Color Palette & Roles\n\nNo bullet points here, only prose.\n"
    assert parser.extract_colors(md) == []


def test_extract_section_fuzzy(sample_design_md: str) -> None:
    parser = DesignMdParser()
    body = parser.extract_section(sample_design_md, "colors")
    assert body is not None
    assert "Stripe Purple" in body
    assert "#533afd" in body


def test_extract_section_exact_name(sample_design_md: str) -> None:
    parser = DesignMdParser()
    body = parser.extract_section(sample_design_md, "Typography Rules")
    assert body is not None
    assert "Sohne" in body or "Inter" in body


def test_extract_section_unknown_returns_none(sample_design_md: str) -> None:
    parser = DesignMdParser()
    assert parser.extract_section(sample_design_md, "nonexistent zzz") is None


def test_parse_empty_returns_empty_sections() -> None:
    parser = DesignMdParser()
    result = parser.parse("")
    assert result["sections"] == {}
    assert result["colors"] == []
    assert result["raw"] == ""


def test_parse_no_h2_returns_empty_sections() -> None:
    parser = DesignMdParser()
    result = parser.parse("Just some text\nwith no headings at all.")
    assert result["sections"] == {}


def test_parse_file_round_trip(stripe_fixture_path) -> None:
    parser = DesignMdParser()
    result = parser.parse_file(stripe_fixture_path)
    assert "Color Palette & Roles" in result["sections"]
    assert any(c["hex"] == "#533afd" for c in result["colors"])


def test_extract_colors_regex_tolerates_uppercase_hex() -> None:
    parser = DesignMdParser()
    md = "- **Foo** (#AABBCC): test color\n"
    colors = parser.extract_colors(md)
    assert len(colors) == 1
    assert colors[0]["hex"] == "#aabbcc"


def test_extract_colors_backtick_wrapped() -> None:
    """Upstream wraps hex in backticks: `- **Name** (`#533afd`): desc`."""
    parser = DesignMdParser()
    md = "- **Stripe Purple** (`#533afd`): Primary brand color.\n"
    colors = parser.extract_colors(md)
    assert len(colors) == 1
    assert colors[0]["hex"] == "#533afd"
    assert colors[0]["hex_all"] == ["#533afd"]
    assert colors[0]["name"] == "Stripe Purple"


def test_extract_colors_multi_hex_values() -> None:
    """Some bullets list multiple hex values separated by ` / `."""
    parser = DesignMdParser()
    md = "- **Marketing Black** (`#010102` / `#08090a`): Hero backgrounds.\n"
    colors = parser.extract_colors(md)
    assert len(colors) == 1
    assert colors[0]["hex"] == "#010102"
    assert colors[0]["hex_all"] == ["#010102", "#08090a"]


def test_extract_colors_rgba_mixed_with_hex() -> None:
    """rgba() with nested parens must not break the line parse."""
    parser = DesignMdParser()
    md = "- **Smoke** (`rgba(0,0,0,0.95)` / `#000000f2`): Overlay scrim.\n"
    colors = parser.extract_colors(md)
    assert len(colors) == 1
    assert colors[0]["hex"] == "#000000f2"
    assert colors[0]["description"] == "Overlay scrim."


def test_extract_colors_rgba_only_is_skipped() -> None:
    """Bullets with no hex (pure rgba) are skipped — we only canonicalise hex."""
    parser = DesignMdParser()
    md = "- **Translucent** (`rgba(0,0,0,0.5)`): Pure rgba, no hex.\n"
    colors = parser.extract_colors(md)
    assert colors == []
