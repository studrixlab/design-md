"""FastMCP server exposing ``design-md`` to Claude Code and other MCP clients.

This module is intentionally a thin adapter over :mod:`design_md.catalog`,
:mod:`design_md.cache`, and :mod:`design_md.parser`. It has a single optional
dependency (``mcp``) and can be launched with::

    python -m design_md.mcp_server

Register it in ``~/.claude/settings.json`` (or ``.mcp.json`` at project root)::

    {
      "mcpServers": {
        "design-md": {
          "command": "python",
          "args": ["-m", "design_md.mcp_server"]
        }
      }
    }

The server exposes four tools; all accept plain arguments and return JSON-
compatible dicts so Claude Code surfaces them cleanly in tool results.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from design_md import __version__
from design_md.cache import DataCache
from design_md.catalog import (
    SECTORS,
    all_sites,
    get_sector,
    is_known_site,
    list_sites,
    sectors,
)
from design_md.parser import DesignMdParser

logger = logging.getLogger("design_md.mcp_server")

mcp = FastMCP("design-md")

# Singleton cache/parser — cheap to create but stable between tool calls.
_cache = DataCache()
_parser = DesignMdParser()


def _not_initialised_payload() -> dict[str, Any]:
    """Return a structured error when the submodule is missing.

    Returns:
        Dict with ``error`` and ``hint`` keys.
    """
    return {
        "error": "data_not_initialised",
        "hint": _cache.init_hint(),
    }


@mcp.tool()
def design_md_list(sector: str | None = None) -> dict[str, Any]:
    """List the available design system sites.

    Args:
        sector: Optional sector key to filter by (e.g. ``"ai"``, ``"dev"``).
            Valid keys: ai, auto, consumer, design, dev, fintech, infra.

    Returns:
        Dict with ``count``, ``sites``, ``sector``, and the full list of
        available sector keys.
    """
    if sector is not None and sector.lower() not in SECTORS:
        return {
            "error": "unknown_sector",
            "sector": sector,
            "valid_sectors": sectors(),
        }
    sites = list_sites(sector)
    return {
        "count": len(sites),
        "sector": sector,
        "sites": sites,
        "sectors": sectors(),
    }


@mcp.tool()
def design_md_get(site: str, section: str | None = None) -> dict[str, Any]:
    """Fetch the DESIGN.md for a given site, or a single section of it.

    Args:
        site: Site identifier (e.g. ``"stripe"``, ``"notion"``, ``"linear.app"``).
        section: Optional section name or fragment. Fuzzy matching is used,
            so ``"colors"`` resolves to ``"Color Palette & Roles"``.

    Returns:
        Dict with the parsed design system. When ``section`` is provided, the
        response contains only the requested section body; otherwise the full
        structured parse (sections + colors) is returned.
    """
    site_lower = site.lower()
    if not is_known_site(site_lower):
        return {
            "error": "unknown_site",
            "site": site,
            "hint": "Call design_md_list() to see available sites.",
        }

    if not _cache.is_initialized():
        return _not_initialised_payload()

    design_path = _cache.get_design_path(site_lower)
    if design_path is None:
        return {
            "error": "design_not_found_on_disk",
            "site": site_lower,
            "hint": "Run `git submodule update --remote data/awesome-design-md`.",
        }

    try:
        parsed = _parser.parse_file(design_path)
    except OSError as err:
        logger.debug("Failed to read %s: %s", design_path, err)
        return {
            "error": "io_error",
            "site": site_lower,
            "detail": str(err),
        }

    if section:
        body = _parser.extract_section(parsed["raw"], section)
        if body is None:
            return {
                "error": "section_not_found",
                "site": site_lower,
                "requested": section,
                "available": list(parsed["sections"].keys()),
            }
        return {
            "site": site_lower,
            "sector": get_sector(site_lower),
            "section": section,
            "body": body,
        }

    return {
        "site": site_lower,
        "sector": get_sector(site_lower),
        "sections": parsed["sections"],
        "colors": parsed["colors"],
    }


@mcp.tool()
def design_md_search(query: str, limit: int = 20) -> dict[str, Any]:
    """Grep across every locally available DESIGN.md file.

    Case-insensitive substring match. Useful when the caller knows a colour,
    token name, or concept and wants to find which design systems mention it.

    Args:
        query: Substring to search for (case-insensitive).
        limit: Maximum number of hits to return (default 20, min 1).

    Returns:
        Dict with ``count`` and a ``hits`` list of ``{site, line_no, snippet}``.
    """
    if limit < 1:
        return {"error": "invalid_limit", "hint": "limit must be >= 1"}
    if not query.strip():
        return {"error": "empty_query"}
    if not _cache.is_initialized():
        return _not_initialised_payload()

    hits = _cache.search(query, limit=limit)
    return {
        "query": query,
        "count": len(hits),
        "hits": hits,
    }


@mcp.tool()
def design_md_info() -> dict[str, Any]:
    """Return basic metadata about the design-md catalog and local state.

    Returns:
        Dict with ``version``, ``total_sites``, ``initialised``, and
        ``sectors``.
    """
    return {
        "version": __version__,
        "total_sites": len(all_sites()),
        "initialised": _cache.is_initialized(),
        "data_root": str(_cache.data_root),
        "sectors": {k: len(v) for k, v in SECTORS.items()},
    }


def main() -> None:
    """Run the MCP server over stdio (used by ``python -m design_md.mcp_server``)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info("Starting design-md MCP server v%s", __version__)
    mcp.run()


if __name__ == "__main__":
    main()
