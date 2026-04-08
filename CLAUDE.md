# design-md — Wrapper VoltAgent/awesome-design-md

## Version
0.1.0 (alpha — local only, pas encore déployé)

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
| `data/awesome-design-md/` | Submodule git (NON tracké directement, ajouté par opérateur) |
| `tests/` | pytest, fixture stripe minimaliste, smoke tests CLI |

## Conventions
- Python 3.11+, **stdlib only** (zéro dépendance runtime).
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
sur les 58 sites :

1. `## Visual Theme & Atmosphere`
2. `## Color Palette & Roles`
3. `## Typography Rules`
4. `## Component Stylings`
5. `## Layout Principles`
6. `## Depth & Elevation`
7. `## Do's and Don'ts`
8. `## Responsive Behavior`
9. `## Agent Prompt Guide`

Couleurs : `- **Name** (#hex): Description`
Regex utilisée : `r'-\s*\*\*([^*]+)\*\*\s*\(([#0-9a-fA-F]+)\):\s*(.*)'`

## Infrastructure
Source de vérité : `/opt/jarvis/INFRA_MAP.md` (CX33).
- CX33 (10.44.0.1) : CERVEAU
- AX102 (10.44.0.2) : ATELIER (déploiement futur sous `/opt/empire/tools/design-md/`)

## State
ALPHA — code écrit, tests à valider par l'orchestrateur.
