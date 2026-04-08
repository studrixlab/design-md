"""Local cache wrapper around the cloned ``awesome-design-md`` data directory.

The :class:`DataCache` class hides filesystem layout from the rest of the
package and exposes simple helpers for catalog lookup, iteration, and grep.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from design_md.catalog import all_sites, site_path

logger = logging.getLogger(__name__)


class DataCache:
    """Filesystem accessor for the bundled ``data/awesome-design-md`` clone.

    The clone itself is added by the operator with::

        git submodule add https://github.com/VoltAgent/awesome-design-md.git \\
            data/awesome-design-md

    The class is intentionally tolerant of a missing clone: callers can use
    :meth:`is_initialized` before invoking the data-accessing methods.
    """

    def __init__(self, data_root: Path | None = None) -> None:
        """Initialise the cache.

        Args:
            data_root: Override path of the local ``data/`` directory. When
                ``None``, defaults to ``<package>/../data``.
        """
        if data_root is None:
            data_root = Path(__file__).resolve().parent.parent / "data"
        self.data_root = Path(data_root)
        self._designs_root = self.data_root / "awesome-design-md" / "design-md"

    @property
    def designs_root(self) -> Path:
        """Root directory containing per-site design folders."""
        return self._designs_root

    def is_initialized(self) -> bool:
        """Return whether the upstream submodule appears to be present.

        Returns:
            True when the ``design-md/`` folder of the clone exists.
        """
        return self._designs_root.is_dir()

    def get_design_path(self, site: str) -> Path | None:
        """Return the path of ``DESIGN.md`` for the given site.

        Args:
            site: Site identifier (e.g. ``"stripe"``).

        Returns:
            Path to the ``DESIGN.md`` file, or ``None`` if not found.
        """
        candidate = site_path(self.data_root, site) / "DESIGN.md"
        if candidate.is_file():
            return candidate
        return None

    def get_site_dir(self, site: str) -> Path | None:
        """Return the directory of a site, if present on disk.

        Args:
            site: Site identifier.

        Returns:
            The directory path or ``None`` if absent.
        """
        candidate = site_path(self.data_root, site)
        if candidate.is_dir():
            return candidate
        return None

    def iter_designs(self) -> Iterator[tuple[str, Path]]:
        """Yield ``(site, design_md_path)`` for every catalog site present on disk.

        Sites that are missing from the local clone are silently skipped.

        Yields:
            Tuples of ``(site_id, path_to_DESIGN.md)``.
        """
        if not self.is_initialized():
            return
        for site in all_sites():
            design = self.get_design_path(site)
            if design is not None:
                yield site, design

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Grep through every available DESIGN.md.

        The match is case-insensitive substring; results are truncated when
        ``limit`` is reached.

        Args:
            query: Search query (case-insensitive substring).
            limit: Maximum number of hits to return.

        Returns:
            List of ``{"site", "line_no", "snippet"}`` dicts.
        """
        results: list[dict] = []
        if not query:
            return results

        needle = query.lower()
        for site, path in self.iter_designs():
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError as err:
                logger.debug("Failed to read %s: %s", path, err)
                continue
            for line_no, line in enumerate(lines, start=1):
                if needle in line.lower():
                    results.append(
                        {
                            "site": site,
                            "line_no": line_no,
                            "snippet": line.strip(),
                        }
                    )
                    if len(results) >= limit:
                        return results
        return results

    def init_hint(self) -> str:
        """Return a user-facing message describing how to populate the cache."""
        return (
            "data/awesome-design-md is missing. Run:\n"
            "  git submodule add https://github.com/VoltAgent/awesome-design-md.git "
            "data/awesome-design-md"
        )
