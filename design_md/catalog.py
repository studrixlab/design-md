"""Catalog of the 58 sites available in VoltAgent/awesome-design-md.

Provides the canonical list of sites, sector mapping, and helpers to resolve
the on-disk path of a given site within the cloned data directory.
"""

from __future__ import annotations

from pathlib import Path

# Hardcoded list of all 58 sites available in the upstream repo (verified 07/04/2026).
ALL_SITES: tuple[str, ...] = (
    "airbnb",
    "airtable",
    "apple",
    "bmw",
    "cal",
    "claude",
    "clay",
    "clickhouse",
    "cohere",
    "coinbase",
    "composio",
    "cursor",
    "elevenlabs",
    "expo",
    "ferrari",
    "figma",
    "framer",
    "hashicorp",
    "ibm",
    "intercom",
    "kraken",
    "lamborghini",
    "linear.app",
    "lovable",
    "minimax",
    "mintlify",
    "miro",
    "mistral.ai",
    "mongodb",
    "notion",
    "nvidia",
    "ollama",
    "opencode.ai",
    "pinterest",
    "posthog",
    "raycast",
    "renault",
    "replicate",
    "resend",
    "revolut",
    "runwayml",
    "sanity",
    "sentry",
    "spacex",
    "spotify",
    "stripe",
    "supabase",
    "superhuman",
    "tesla",
    "together.ai",
    "uber",
    "vercel",
    "voltagent",
    "warp",
    "webflow",
    "wise",
    "x.ai",
    "zapier",
)

# Sector taxonomy. Each site is in exactly one sector.
SECTORS: dict[str, list[str]] = {
    "ai": [
        "claude",
        "cohere",
        "elevenlabs",
        "minimax",
        "mistral.ai",
        "ollama",
        "opencode.ai",
        "replicate",
        "runwayml",
        "together.ai",
        "voltagent",
        "x.ai",
    ],
    "dev": [
        "cursor",
        "expo",
        "linear.app",
        "lovable",
        "mintlify",
        "posthog",
        "raycast",
        "resend",
        "sentry",
        "supabase",
        "superhuman",
        "vercel",
        "warp",
        "zapier",
    ],
    "infra": [
        "clickhouse",
        "composio",
        "hashicorp",
        "mongodb",
        "sanity",
        "stripe",
    ],
    "design": [
        "airtable",
        "cal",
        "clay",
        "figma",
        "framer",
        "intercom",
        "miro",
        "notion",
        "pinterest",
        "webflow",
    ],
    "fintech": [
        "coinbase",
        "kraken",
        "revolut",
        "wise",
    ],
    "consumer": [
        "airbnb",
        "apple",
        "ibm",
        "nvidia",
        "spacex",
        "spotify",
        "uber",
    ],
    "auto": [
        "bmw",
        "ferrari",
        "lamborghini",
        "renault",
        "tesla",
    ],
}


def all_sites() -> list[str]:
    """Return the canonical list of all 58 supported sites.

    Returns:
        New list (a copy) sorted in canonical order.
    """
    return list(ALL_SITES)


def list_sites(sector: str | None = None) -> list[str]:
    """List sites, optionally filtered by sector.

    Args:
        sector: Sector key (e.g. "ai", "dev"). When ``None`` returns all sites.

    Returns:
        Sorted list of site identifiers. Empty if the sector is unknown.
    """
    if sector is None:
        return sorted(ALL_SITES)
    sites = SECTORS.get(sector.lower())
    if sites is None:
        return []
    return sorted(sites)


def get_sector(site: str) -> str | None:
    """Resolve the sector of a given site.

    Args:
        site: Site identifier (e.g. "stripe").

    Returns:
        Sector name, or ``None`` if the site is unknown.
    """
    site_lower = site.lower()
    for sector_name, members in SECTORS.items():
        if site_lower in members:
            return sector_name
    return None


def is_known_site(site: str) -> bool:
    """Return whether a given identifier is part of the catalog.

    Args:
        site: Site identifier to check.

    Returns:
        True when the site is known, False otherwise.
    """
    return site.lower() in ALL_SITES


def site_path(data_root: Path, site: str) -> Path:
    """Compute the on-disk directory path of a given site.

    Args:
        data_root: Path of the local ``data/`` directory.
        site: Site identifier.

    Returns:
        Absolute path to ``<data_root>/awesome-design-md/design-md/<site>``.
    """
    return data_root / "awesome-design-md" / "design-md" / site


def sectors() -> list[str]:
    """Return the sorted list of available sector keys.

    Returns:
        Sorted list of sector keys.
    """
    return sorted(SECTORS.keys())
