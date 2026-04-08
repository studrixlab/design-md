# design-md

Wrapper OS-EMPIRE autour de [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
— accès programmatique aux design systems de 58 sites de référence (Stripe, Linear,
Vercel, Apple, Tesla, ...) pour les agents OS-EMPIRE qui génèrent de l'UI.

## What

`design-md` expose le contenu du repo public `VoltAgent/awesome-design-md` sous
forme de bibliothèque Python + CLI. Pour chaque site (58 au total), on récupère
facilement :

- Le `DESIGN.md` complet (~300 lignes, format "Google Stitch" à 9 sections H2).
- Une section précise (couleurs, typographie, layout, ...).
- La palette de couleurs sous forme structurée (`name`, `hex`, `description`).
- Des recherches grep cross-files (ex: tous les sites qui utilisent `Inter`).

## Why

Les agents OS-EMPIRE (FORGE, studrix-hub, KODEX, Cockpit v6) ont besoin de
références de design cohérentes pour générer de l'UI qui ne ressemble pas à du
"AI slop". `design-md` est l'unique point d'entrée pour récupérer ces refs et
les injecter dans un prompt agent.

## Install

```bash
cd C:/jarvis/tools/design-md
pip install -e .
```

Puis ajoute le contenu en tant que git submodule (le wrapper ne le télécharge
pas automatiquement, par design : on n'embarque pas le clone dans le tracking
direct du repo) :

```bash
git submodule add https://github.com/VoltAgent/awesome-design-md.git data/awesome-design-md
git submodule update --init --recursive
```

## Quick start

```bash
# Liste tous les sites
design-md list

# Filtre par secteur
design-md list --sector ai
design-md list --sector fintech --format json

# Récupère le DESIGN.md complet d'un site
design-md get stripe

# Récupère juste la palette de couleurs
design-md get stripe --section colors

# Sortie JSON pour ingestion agent
design-md get stripe --format json

# Recherche cross-files
design-md search "Inter" --limit 10
```

En Python :

```python
from pathlib import Path
from design_md.cache import DataCache
from design_md.parser import DesignMdParser

cache = DataCache()
parser = DesignMdParser()

design_path = cache.get_design_path("stripe")
parsed = parser.parse_file(design_path)

print(parsed["colors"])
# [{"name": "Stripe Purple", "hex": "#533afd", "description": "..."}]
```

## CLI reference

| Commande | Description |
|----------|-------------|
| `design-md list [--sector S] [--format json/table]` | Liste les sites disponibles |
| `design-md get SITE [--section S] [--format json/md]` | Récupère DESIGN.md ou une section |
| `design-md search QUERY [--limit N] [--format json/table]` | Grep cross-files |
| `design-md update` | Affiche la commande git submodule update à exécuter |
| `design-md --version` | Affiche la version |
| `design-md -v ...` | Active les logs DEBUG |

Codes de sortie : `0` OK, `1` erreur utilisateur (site inconnu, sector invalide, ...), `2` erreur système (lecture fichier impossible, ...).

## Layout

```
design-md/
├── design_md/        # Code package (stdlib only)
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py        # argparse subcommands
│   ├── parser.py     # DesignMdParser regex-based
│   ├── catalog.py    # 58 sites + sectors
│   └── cache.py      # Accès filesystem au submodule
├── data/             # Submodule git VoltAgent/awesome-design-md (non tracké)
├── tests/            # pytest, fixtures incluses
├── pyproject.toml
└── README.md
```

## Secteurs

| Secteur | Sites |
|---------|-------|
| ai | claude, cohere, elevenlabs, minimax, mistral.ai, ollama, opencode.ai, replicate, runwayml, together.ai, voltagent, x.ai |
| dev | cursor, expo, linear.app, lovable, mintlify, posthog, raycast, resend, sentry, supabase, superhuman, vercel, warp, zapier |
| infra | clickhouse, composio, hashicorp, mongodb, sanity, stripe |
| design | airtable, cal, clay, figma, framer, intercom, miro, notion, pinterest, webflow |
| fintech | coinbase, kraken, revolut, wise |
| consumer | airbnb, apple, ibm, nvidia, spacex, spotify, uber |
| auto | bmw, ferrari, lamborghini, renault, tesla |

## License

Code wrapper sous licence MIT (OS-EMPIRE / studrixlab).

Le contenu du dossier `data/awesome-design-md/` provient du repo
[VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
sous licence MIT, copyright VoltAgent contributors. Aucun fichier de ce repo
n'est dupliqué dans `design-md/` : il est référencé exclusivement via git
submodule.
