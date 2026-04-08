# DESIGN-MD — Wrapper VoltAgent/awesome-design-md

**Type**: tool
**Location**: local `C:\jarvis\tools\design-md\` (déploiement AX102 prévu)
**Repo**: https://github.com/studrixlab/design-md
**Status**: ALPHA — 52/52 tests pass
**Created**: 2026-04-07

## Purpose
Donner aux agents OS-EMPIRE un accès programmatique au contenu de
`VoltAgent/awesome-design-md` (58 design systems de référence) pour générer
de l'UI cohérente et non-générique.

## Dependencies
- Python 3.11+
- Core: stdlib only — zéro dépendance runtime
- Optional `[mcp]`: `mcp>=1.0` (FastMCP) pour `design_md/mcp_server.py`
- Git submodule `data/awesome-design-md` (tracké via `.gitmodules`)

## Key files
- `design_md/cli.py` — entry point, subcommands list/get/search/update
- `design_md/parser.py` — `DesignMdParser` regex-based (simple/multi/rgba)
- `design_md/catalog.py` — 58 sites + 7 secteurs
- `design_md/cache.py` — `DataCache`, accès filesystem au submodule
- `design_md/mcp_server.py` — FastMCP, 4 tools (list/get/search/info)
- `tests/fixtures/stripe_DESIGN.md` — fixture avec 3 formats de couleurs

## How agents use it
```python
from design_md.cache import DataCache
from design_md.parser import DesignMdParser

cache = DataCache()
parser = DesignMdParser()

if not cache.is_initialized():
    raise RuntimeError(cache.init_hint())

design_path = cache.get_design_path("stripe")
parsed = parser.parse_file(design_path)

# Inject directly into agent prompt
palette = parsed["colors"]
typography = parsed["sections"]["Typography Rules"]
```

Ou via CLI dans un workflow shell :
```bash
design-md get stripe --section colors --format json | jq .
```

Ou via MCP server (pour Claude Code) — enregistrer dans `~/.claude/settings.json` :
```json
{
  "mcpServers": {
    "design-md": {
      "command": "python",
      "args": ["-m", "design_md.mcp_server"]
    }
  }
}
```
Tools exposés : `design_md_list`, `design_md_get`, `design_md_search`, `design_md_info`.
