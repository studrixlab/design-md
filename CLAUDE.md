# design-md — Wrapper VoltAgent/awesome-design-md

## Version
0.1.0 (alpha — local + remote studrixlab/design-md, pas encore déployé AX102)

## Purpose
Wrapper Python (stdlib only) qui expose le contenu du repo public
`VoltAgent/awesome-design-md` (58 design systems) sous forme de bibliothèque +
CLI consommable par les agents OS-EMPIRE qui génèrent de l'UI.

## Architecture
| Module | Responsabilité |
|--------|---------------|
| `design_md/cli.py` | Subcommands argparse: list, get, search, update |
| `design_md/parser.py` | `DesignMdParser` regex-based — 0 dépendance markdown |
| `design_md/catalog.py` | Liste hardcodée des 58 sites + mapping sector |
| `design_md/cache.py` | `DataCache` — accès filesystem au submodule git |
| `design_md/mcp_server.py` | FastMCP server — 4 tools (optional dep `mcp`) |
| `data/awesome-design-md/` | Submodule git trackée via `.gitmodules` |
| `tests/` | pytest, fixture stripe multi-format, 52 tests |

## Conventions
- Python 3.11+, **stdlib only** pour le core (zéro dépendance runtime).
- Seule exception : `mcp_server.py` importe le package `mcp` (FastMCP),
  déclaré en optional dep `[mcp]`.
- argparse (PAS click ni typer).
- Type hints partout, docstrings Google style.
- Logging stdlib (`logging.getLogger(__name__)`), pas de `print()` sauf
  output utilisateur du CLI.
- Codes de sortie : 0 OK, 1 erreur utilisateur, 2 erreur système.
- Pas de stub (`pass`) — règle G3 OS-EMPIRE. Méthodes vides → `return None`
  ou `logger.debug(...)`.
- Pas de subprocess git interne — l'opérateur ajoute le submodule lui-même.

## Lint / Test commands
```bash
ruff check design_md tests
ruff format --check design_md tests
pytest tests -v
```

## Deployment notes
- Disponible en local uniquement pour le moment.
- Pas de remote GitHub configuré (sera fait après validation Kevin).
- Pas de service systemd, pas de container : c'est un CLI local + lib Python.
- Quand on déploiera sur AX102 : `pip install -e .` + `git submodule update
  --init` dans `/opt/empire/tools/design-md/`.

## Format DESIGN.md upstream
Les fichiers `DESIGN.md` du repo VoltAgent suivent un format consistant à 100%
sur les 58 sites, avec sections numérotées :

1. `## 1. Visual Theme & Atmosphere`
2. `## 2. Color Palette & Roles`
3. `## 3. Typography Rules`
4. `## 4. Component Stylings`
5. `## 5. Layout Principles`
6. `## 6. Depth & Elevation`
7. `## 7. Do's and Don'ts`
8. `## 8. Responsive Behavior`
9. `## 9. Agent Prompt Guide`

Couleurs (3 formats réels) :
- Simple : `` - **Name** (`#533afd`): Description ``
- Multi-hex : `` - **Name** (`#010102` / `#08090a`): Description ``
- Avec rgba : `` - **Name** (`rgba(0,0,0,0.95)` / `#000000f2`): Description ``

Parser : `_COLOR_LINE_RE` extrait name/values_blob/description, puis
`_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}")` extrait tous les hex du blob.
Les bullets pure-rgba (sans hex) sont volontairement skipped.

## Infrastructure
Source de vérité : `/opt/jarvis/INFRA_MAP.md` (CX33).
- CX33 (10.44.0.1) : CERVEAU
- AX102 (10.44.0.2) : ATELIER (déploiement futur sous `/opt/empire/tools/design-md/`)

## State
ALPHA — code écrit, 52/52 tests pass, ruff clean, format clean.
Remote push : https://github.com/studrixlab/design-md

## Version history
- **0.1.0** (2026-04-08) — Initial release. CLI + FastMCP server, 52 tests,
  parser gère les 3 formats réels (simple/multi-hex/rgba).
