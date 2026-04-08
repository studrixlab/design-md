"""CLI entry point for the ``design-md`` tool."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from design_md import __version__
from design_md.cache import DataCache
from design_md.catalog import (
    SECTORS,
    get_sector,
    is_known_site,
    list_sites,
    sectors,
)
from design_md.parser import DesignMdParser

EXIT_OK = 0
EXIT_USER_ERROR = 1
EXIT_SYSTEM_ERROR = 2


def _setup_logging(verbose: bool) -> None:
    """Configure stdlib logging.

    Args:
        verbose: When True, set the root level to DEBUG. Otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _err(message: str) -> None:
    """Write a user-facing error message to stderr.

    Args:
        message: Pre-formatted error string.
    """
    sys.stderr.write(f"error: {message}\n")


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser with all subcommands.

    Returns:
        Configured ``argparse.ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        prog="design-md",
        description=(
            "design-md — Wrapper OS-EMPIRE around VoltAgent/awesome-design-md. "
            "Programmatic access to 58 design systems for UI generation agents."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"design-md {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--data-root",
        type=str,
        default=None,
        help="Override the local data/ directory (advanced)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- list ----
    list_parser = subparsers.add_parser(
        "list",
        help="List available sites, optionally filtered by sector",
    )
    list_parser.add_argument(
        "--sector",
        type=str,
        default=None,
        help=f"Filter by sector. One of: {', '.join(sectors())}",
    )
    list_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Output format (default: table)",
    )

    # ---- get ----
    get_parser = subparsers.add_parser(
        "get",
        help="Read the DESIGN.md of a given site (or one of its sections)",
    )
    get_parser.add_argument("site", type=str, help="Site identifier (e.g. stripe)")
    get_parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Extract a single section (fuzzy match, e.g. colors)",
    )
    get_parser.add_argument(
        "--format",
        choices=["json", "md"],
        default="md",
        help="Output format (default: md)",
    )

    # ---- search ----
    search_parser = subparsers.add_parser(
        "search",
        help="Grep across all DESIGN.md files",
    )
    search_parser.add_argument("query", type=str, help="Substring to search (case-insensitive)")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of hits (default: 20)",
    )
    search_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Output format (default: table)",
    )

    # ---- update ----
    subparsers.add_parser(
        "update",
        help="Print the git submodule update command (does not run it)",
    )

    return parser


def _cmd_list(args: argparse.Namespace) -> int:
    """Handle the ``list`` subcommand.

    Args:
        args: Parsed CLI namespace.

    Returns:
        Process exit code.
    """
    if args.sector and args.sector.lower() not in SECTORS:
        _err(f"Unknown sector: {args.sector}. Valid: {', '.join(sectors())}")
        return EXIT_USER_ERROR

    sites = list_sites(args.sector)

    if args.format == "json":
        payload = {
            "sector": args.sector,
            "count": len(sites),
            "sites": sites,
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return EXIT_OK

    if not sites:
        sys.stdout.write("(no sites)\n")
        return EXIT_OK

    header = f"Sites ({len(sites)})"
    if args.sector:
        header += f" — sector: {args.sector}"
    sys.stdout.write(header + "\n")
    sys.stdout.write("-" * len(header) + "\n")
    for site in sites:
        sector_name = get_sector(site) or "?"
        sys.stdout.write(f"  {site:<18} [{sector_name}]\n")
    return EXIT_OK


def _cmd_get(args: argparse.Namespace, cache: DataCache) -> int:
    """Handle the ``get`` subcommand.

    Args:
        args: Parsed CLI namespace.
        cache: Initialised :class:`DataCache`.

    Returns:
        Process exit code.
    """
    site = args.site.lower()
    if not is_known_site(site):
        _err(f"Unknown site: {args.site}. Use `design-md list` to see available sites.")
        return EXIT_USER_ERROR

    if not cache.is_initialized():
        _err(cache.init_hint())
        return EXIT_USER_ERROR

    design_path = cache.get_design_path(site)
    if design_path is None:
        _err(f"DESIGN.md not found for {site} under {cache.designs_root}. Try: design-md update")
        return EXIT_SYSTEM_ERROR

    parser = DesignMdParser()
    try:
        parsed = parser.parse_file(design_path)
    except OSError as err:
        _err(f"Failed to read {design_path}: {err}")
        return EXIT_SYSTEM_ERROR

    if args.section:
        body = parser.extract_section(parsed["raw"], args.section)
        if body is None:
            available = ", ".join(parsed["sections"].keys())
            _err(f"Section {args.section!r} not found in {site}. Available: {available}")
            return EXIT_USER_ERROR
        if args.format == "json":
            payload = {"site": site, "section": args.section, "body": body}
            sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        else:
            sys.stdout.write(body + "\n")
        return EXIT_OK

    if args.format == "json":
        payload = {
            "site": site,
            "sector": get_sector(site),
            "sections": parsed["sections"],
            "colors": parsed["colors"],
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    else:
        sys.stdout.write(parsed["raw"])
        if not parsed["raw"].endswith("\n"):
            sys.stdout.write("\n")
    return EXIT_OK


def _cmd_search(args: argparse.Namespace, cache: DataCache) -> int:
    """Handle the ``search`` subcommand.

    Args:
        args: Parsed CLI namespace.
        cache: Initialised :class:`DataCache`.

    Returns:
        Process exit code.
    """
    if args.limit < 1:
        _err("--limit must be >= 1")
        return EXIT_USER_ERROR

    if not cache.is_initialized():
        _err(cache.init_hint())
        return EXIT_USER_ERROR

    hits = cache.search(args.query, limit=args.limit)

    if args.format == "json":
        payload = {"query": args.query, "count": len(hits), "hits": hits}
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return EXIT_OK

    if not hits:
        sys.stdout.write(f"No results for {args.query!r}\n")
        return EXIT_OK

    sys.stdout.write(f"{len(hits)} hit(s) for {args.query!r}\n")
    for hit in hits:
        sys.stdout.write(f"  {hit['site']}:{hit['line_no']}  {hit['snippet']}\n")
    return EXIT_OK


def _cmd_update(_args: argparse.Namespace) -> int:
    """Handle the ``update`` subcommand (advisory only).

    Returns:
        Always ``EXIT_OK``.
    """
    sys.stdout.write(
        "design-md does not auto-update the data submodule.\n"
        "Run one of:\n"
        "  git submodule update --remote data/awesome-design-md\n"
        "Or, if the submodule is not yet added:\n"
        "  git submodule add https://github.com/VoltAgent/awesome-design-md.git "
        "data/awesome-design-md\n"
    )
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Top-level entry point.

    Args:
        argv: Optional argument vector for testing. ``None`` uses ``sys.argv``.

    Returns:
        Process exit code (0 OK, 1 user error, 2 system error).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    cache_kwargs: dict = {}
    if args.data_root:
        cache_kwargs["data_root"] = Path(args.data_root)
    cache = DataCache(**cache_kwargs)

    if args.command == "list":
        return _cmd_list(args)
    if args.command == "get":
        return _cmd_get(args, cache)
    if args.command == "search":
        return _cmd_search(args, cache)
    if args.command == "update":
        return _cmd_update(args)

    parser.print_help()
    return EXIT_USER_ERROR
