"""Smoke tests for the FastMCP server wrapper.

These tests import the tool functions directly (bypassing the MCP transport
layer) so the suite stays fast and stdio-free. The goal is to guarantee the
server contract: every tool returns a JSON-serialisable dict, error branches
trigger the expected ``error`` keys, and the happy path wires through to the
real catalog / parser / cache.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ``mcp`` is an optional dep. Skip the entire module if it is missing.
mcp_pkg = pytest.importorskip("mcp", reason="mcp package not installed")

from design_md import mcp_server  # noqa: E402


@pytest.fixture(autouse=True)
def _point_cache_at(tmp_data_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect the module-level cache to the test fixture tree."""
    from design_md.cache import DataCache

    monkeypatch.setattr(mcp_server, "_cache", DataCache(data_root=tmp_data_root))


def _roundtrip_json(payload: dict) -> dict:
    """Assert that ``payload`` is JSON-serialisable and return the roundtrip."""
    return json.loads(json.dumps(payload))


def test_info_reports_catalog_metadata() -> None:
    result = mcp_server.design_md_info()
    _roundtrip_json(result)
    assert result["total_sites"] == 58
    assert result["initialised"] is True
    assert "ai" in result["sectors"]
    assert result["sectors"]["ai"] == 12


def test_list_returns_sites_for_valid_sector() -> None:
    result = mcp_server.design_md_list("ai")
    _roundtrip_json(result)
    assert result["sector"] == "ai"
    assert result["count"] > 0
    assert "claude" in result["sites"]


def test_list_rejects_unknown_sector() -> None:
    result = mcp_server.design_md_list("nope")
    assert result["error"] == "unknown_sector"
    assert "valid_sectors" in result


def test_list_without_sector_returns_all() -> None:
    result = mcp_server.design_md_list(None)
    assert result["count"] == 58


def test_get_unknown_site_returns_error() -> None:
    result = mcp_server.design_md_get("not_a_real_site_xyz")
    assert result["error"] == "unknown_site"


def test_get_known_site_returns_parsed_payload() -> None:
    result = mcp_server.design_md_get("stripe")
    _roundtrip_json(result)
    assert result["site"] == "stripe"
    assert result["sector"] == "infra"
    assert isinstance(result["sections"], dict)
    assert len(result["sections"]) == 9
    assert len(result["colors"]) >= 3


def test_get_section_returns_body_only() -> None:
    result = mcp_server.design_md_get("stripe", "colors")
    _roundtrip_json(result)
    assert result["section"] == "colors"
    assert "body" in result
    assert "Stripe Purple" in result["body"]


def test_get_missing_section_reports_available() -> None:
    result = mcp_server.design_md_get("stripe", "totally_fake_section_zzz")
    assert result["error"] == "section_not_found"
    assert isinstance(result["available"], list)
    assert len(result["available"]) == 9


def test_search_finds_substring() -> None:
    result = mcp_server.design_md_search("Stripe Purple", limit=5)
    _roundtrip_json(result)
    assert result["count"] >= 1
    assert any(hit["site"] == "stripe" for hit in result["hits"])


def test_search_rejects_empty_query() -> None:
    result = mcp_server.design_md_search("   ", limit=5)
    assert result["error"] == "empty_query"


def test_search_rejects_invalid_limit() -> None:
    result = mcp_server.design_md_search("x", limit=0)
    assert result["error"] == "invalid_limit"


def test_all_tools_are_registered_on_fastmcp_instance() -> None:
    """Contract check: the four @mcp.tool decorators stay in sync with the module."""
    import asyncio

    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = {t.name for t in tools}
    assert names == {
        "design_md_list",
        "design_md_get",
        "design_md_search",
        "design_md_info",
    }
