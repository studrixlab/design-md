"""Regex-based parser for VoltAgent ``DESIGN.md`` files.

The DESIGN.md format used by ``VoltAgent/awesome-design-md`` is consistent
across the 58 sites: H2 sections in a fixed order with a "Color Palette &
Roles" block listing colours as ``- **Name** (#hex): Description``.

This module exposes :class:`DesignMdParser` which extracts:

* The full set of H2 sections (name -> raw text body).
* A typed list of colours from the palette section.
* Helpers for fuzzy section lookup (e.g. ``"colors"`` -> the palette section).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Canonical section order, lowercased for matching.
CANONICAL_SECTIONS: tuple[str, ...] = (
    "Visual Theme & Atmosphere",
    "Color Palette & Roles",
    "Typography Rules",
    "Component Stylings",
    "Layout Principles",
    "Depth & Elevation",
    "Do's and Don'ts",
    "Responsive Behavior",
    "Agent Prompt Guide",
)

# Match an H2 heading line: "## Title" (no anchor extraction needed here).
_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# Match a colour bullet. The real VoltAgent format wraps hex values in backticks
# and can list multiple values (e.g. ``(`#010102` / `#08090a`)``) or mix in
# ``rgba(...)`` notation with nested parens. We split into two passes:
#   1. ``_COLOR_LINE_RE`` extracts ``name``, ``values_blob``, ``description``.
#   2. ``_HEX_RE`` pulls every hex code out of ``values_blob``.
_COLOR_LINE_RE = re.compile(r"^\s*-\s*\*\*([^*]+)\*\*\s*\((.*)\):\s*(.*)$")
_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}")


class DesignMdParser:
    """Parser for the canonical VoltAgent DESIGN.md format.

    All methods are pure functions of their input string; instances hold no
    state and are cheap to create.
    """

    def parse(self, content: str) -> dict:
        """Parse a full DESIGN.md document.

        Args:
            content: Raw markdown contents of a DESIGN.md file.

        Returns:
            Dict with keys:
              ``sections`` — mapping of section name -> body text,
              ``colors`` — list of ``{name, hex, description}`` dicts,
              ``raw`` — the original input string.
        """
        sections = self._split_sections(content)
        palette_text = self._find_palette_text(sections)
        colors = self.extract_colors(palette_text) if palette_text else []
        return {
            "sections": sections,
            "colors": colors,
            "raw": content,
        }

    def parse_file(self, path: Path) -> dict:
        """Parse a DESIGN.md file from disk.

        Args:
            path: Path to a DESIGN.md file.

        Returns:
            Same shape as :meth:`parse`.

        Raises:
            FileNotFoundError: When the path does not exist.
        """
        text = path.read_text(encoding="utf-8")
        return self.parse(text)

    def extract_section(self, content: str, section_name: str) -> str | None:
        """Extract a single section by (fuzzy) name.

        The lookup is case-insensitive and uses substring matching against the
        canonical section list, then against the actual section names found in
        the document.

        Args:
            content: Raw markdown contents.
            section_name: Section title or fragment (e.g. ``"colors"``).

        Returns:
            The section body, or ``None`` when no section matches.
        """
        sections = self._split_sections(content)
        if not sections:
            return None
        target = self._resolve_section_name(section_name, list(sections.keys()))
        if target is None:
            return None
        return sections.get(target)

    def extract_colors(self, content: str) -> list[dict]:
        """Extract colours from a markdown chunk.

        The chunk can be a full document or just the palette section. The
        parser tolerates several real-world shapes found in the upstream
        ``awesome-design-md`` corpus:

        * Backtick-wrapped hex: ``- **Stripe Purple** (`#533afd`): ...``
        * Multi-value: ``- **Foo** (`#010102` / `#08090a`): ...``
        * Mixed rgba + hex: ``- **Bar** (`rgba(0,0,0,0.95)` / `#000000f2`): ...``

        Only bullets that contain at least one hex code end up in the output;
        colours expressed solely as ``rgba()`` are skipped (they have no
        canonical hex we can normalise to).

        Args:
            content: Markdown text.

        Returns:
            List of dicts with ``name``, ``hex``, ``hex_all``, ``description``.
            ``hex`` is the first hex found (canonical pick); ``hex_all`` is the
            ordered list of every hex discovered on the line.
        """
        out: list[dict] = []
        for line in content.splitlines():
            match = _COLOR_LINE_RE.match(line)
            if not match:
                continue
            name, values_blob, description = match.groups()
            hex_values = [h.lower() for h in _HEX_RE.findall(values_blob)]
            if not hex_values:
                continue
            out.append(
                {
                    "name": name.strip(),
                    "hex": hex_values[0],
                    "hex_all": hex_values,
                    "description": description.strip(),
                }
            )
        return out

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _split_sections(self, content: str) -> dict[str, str]:
        """Split a DESIGN.md document into ``{section_name: body}``.

        Args:
            content: Raw markdown.

        Returns:
            Ordered dict (insertion order) of sections found in the document.
        """
        if not content:
            return {}

        matches = list(_H2_RE.finditer(content))
        if not matches:
            return {}

        sections: dict[str, str] = {}
        for idx, match in enumerate(matches):
            name = match.group(1).strip()
            body_start = match.end()
            body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            body = content[body_start:body_end].strip("\n")
            sections[name] = body
        return sections

    def _find_palette_text(self, sections: dict[str, str]) -> str | None:
        """Locate the palette section body inside a parsed sections dict.

        Args:
            sections: Mapping returned by :meth:`_split_sections`.

        Returns:
            Section body text, or ``None`` when no palette-like section exists.
        """
        for name, body in sections.items():
            lower = name.lower()
            if "color" in lower and ("palette" in lower or "role" in lower):
                return body
        # Fallback: any section that mentions "color" in its title.
        for name, body in sections.items():
            if "color" in name.lower():
                return body
        return None

    def _resolve_section_name(
        self,
        query: str,
        available: list[str],
    ) -> str | None:
        """Resolve a fuzzy query to one of the available section names.

        Strategy (first match wins):
          1. Exact match (case-insensitive).
          2. Substring of an available name (e.g. ``colors`` -> ``Color Palette & Roles``).
          3. Substring of a canonical name (case-insensitive) that also appears
             in ``available``.

        Args:
            query: User-provided section query.
            available: Section names actually present in the document.

        Returns:
            One of ``available``, or ``None`` if nothing matches.
        """
        q = query.strip().lower()
        if not q:
            return None

        for name in available:
            if name.lower() == q:
                return name

        for name in available:
            if q in name.lower():
                return name

        # Try plural/singular trimming for common words.
        q_singular = q.rstrip("s")
        if q_singular and q_singular != q:
            for name in available:
                if q_singular in name.lower():
                    return name

        for canonical in CANONICAL_SECTIONS:
            if q in canonical.lower():
                for name in available:
                    if name.lower() == canonical.lower():
                        return name
        return None
