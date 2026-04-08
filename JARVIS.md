# DESIGN-MD — Wrapper VoltAgent/awesome-design-md

**Type**: tool
**Location**: local `C:\jarvis\tools\design-md\` (déploiement AX102 prévu)
**Repo**: pas encore de remote
**Status**: ALPHA
**Created**: 2026-04-07

## Purpose
Donner aux agents OS-EMPIRE un accès programmatique au contenu de
`VoltAgent/awesome-design-md` (58 design systems de référence) pour générer
de l'UI cohérente et non-générique.

## Dependencies
- Python 3.11+
- Stdlib only — zéro dépendance runtime
- Git submodule `data/awesome-design-md` (ajouté hors wrapper par l'opérateur)

## Key files
- `design_md/cli.py` — entry point, subcommands list/get/search/update
- `design_md/parser.py` — `DesignMdParser` regex-based
- `design_md/catalog.py` — 58 sites + 7 secteurs
- `design_md/cache.py` — `DataCache`, accès filesystem au submodule
- `tests/fixtures/stripe_DESIGN.md` — fixture minimaliste 9 sections

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
