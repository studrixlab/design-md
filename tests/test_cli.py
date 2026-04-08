"""Smoke tests for the design_md CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from design_md.cli import EXIT_OK, EXIT_USER_ERROR, main


def test_cli_list_runs(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["list"])
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "stripe" in out
    assert "claude" in out


def test_cli_list_sector_filter(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["list", "--sector", "ai", "--format", "json"])
    assert code == EXIT_OK
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["sector"] == "ai"
    assert "claude" in payload["sites"]
    assert "stripe" not in payload["sites"]
    assert payload["count"] == len(payload["sites"])


def test_cli_list_unknown_sector(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["list", "--sector", "totally-fake"])
    assert code == EXIT_USER_ERROR


def test_cli_get_missing_data_helpful_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        ["--data-root", str(tmp_path / "empty"), "get", "stripe"],
    )
    assert code == EXIT_USER_ERROR
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "awesome-design-md" in combined


def test_cli_get_unknown_site(
    tmp_data_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        ["--data-root", str(tmp_data_root), "get", "not-a-site"],
    )
    assert code == EXIT_USER_ERROR


def test_cli_get_with_fixture_data(
    tmp_data_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["--data-root", str(tmp_data_root), "get", "stripe"])
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "Stripe Design System" in out
    assert "Stripe Purple" in out


def test_cli_get_section_with_fixture_data(
    tmp_data_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "--data-root",
            str(tmp_data_root),
            "get",
            "stripe",
            "--section",
            "colors",
        ],
    )
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "Stripe Purple" in out
    assert "#533afd" in out


def test_cli_get_section_json(
    tmp_data_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "--data-root",
            str(tmp_data_root),
            "get",
            "stripe",
            "--section",
            "Typography Rules",
            "--format",
            "json",
        ],
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["site"] == "stripe"
    assert payload["section"] == "Typography Rules"
    assert payload["body"]


def test_cli_get_full_json(
    tmp_data_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "--data-root",
            str(tmp_data_root),
            "get",
            "stripe",
            "--format",
            "json",
        ],
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["site"] == "stripe"
    assert payload["sector"] == "infra"
    assert "Color Palette & Roles" in payload["sections"]
    assert any(c["hex"] == "#533afd" for c in payload["colors"])


def test_cli_search_with_fixture_data(
    tmp_data_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "--data-root",
            str(tmp_data_root),
            "search",
            "Stripe Purple",
        ],
    )
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "stripe:" in out


def test_cli_search_json(
    tmp_data_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "--data-root",
            str(tmp_data_root),
            "search",
            "Sohne",
            "--format",
            "json",
        ],
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["query"] == "Sohne"
    assert payload["count"] >= 1


def test_cli_update_prints_command(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["update"])
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "git submodule" in out
    assert "awesome-design-md" in out
