"""Tests for design_md.catalog."""

from __future__ import annotations

from pathlib import Path

from design_md.catalog import (
    ALL_SITES,
    SECTORS,
    all_sites,
    get_sector,
    is_known_site,
    list_sites,
    sectors,
    site_path,
)


def test_all_sites_count_is_58() -> None:
    assert len(ALL_SITES) == 58
    assert len(all_sites()) == 58


def test_all_sites_unique() -> None:
    assert len(set(ALL_SITES)) == 58


def test_list_sites_by_sector_ai() -> None:
    ai_sites = list_sites("ai")
    assert "claude" in ai_sites
    assert "mistral.ai" in ai_sites
    assert "stripe" not in ai_sites
    assert ai_sites == sorted(ai_sites)


def test_list_sites_by_unknown_sector_is_empty() -> None:
    assert list_sites("nope") == []


def test_list_sites_no_filter_returns_all() -> None:
    assert len(list_sites()) == 58


def test_get_sector_known_site() -> None:
    assert get_sector("stripe") == "infra"
    assert get_sector("claude") == "ai"
    assert get_sector("tesla") == "auto"


def test_get_sector_unknown_site_returns_none() -> None:
    assert get_sector("never-heard-of-it") is None


def test_get_sector_case_insensitive() -> None:
    assert get_sector("STRIPE") == "infra"


def test_all_sites_have_a_sector() -> None:
    for site in ALL_SITES:
        sector = get_sector(site)
        assert sector is not None, f"{site} has no sector"
        assert sector in SECTORS


def test_sectors_listing_matches_keys() -> None:
    assert set(sectors()) == set(SECTORS.keys())


def test_is_known_site() -> None:
    assert is_known_site("stripe") is True
    assert is_known_site("STRIPE") is True
    assert is_known_site("definitely-not-a-site") is False


def test_site_path_layout(tmp_path: Path) -> None:
    p = site_path(tmp_path / "data", "stripe")
    assert p.parts[-3:] == ("awesome-design-md", "design-md", "stripe")


def test_each_site_appears_in_exactly_one_sector() -> None:
    seen: dict[str, str] = {}
    for sector_name, members in SECTORS.items():
        for site in members:
            assert site not in seen, f"{site} in both {seen[site]} and {sector_name}"
            seen[site] = sector_name
    assert set(seen.keys()) == set(ALL_SITES)
