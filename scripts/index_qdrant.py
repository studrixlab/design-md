#!/usr/bin/env python3
"""Index every DESIGN.md section into the Qdrant ``design_systems`` collection.

Usage::

    python3 scripts/index_qdrant.py

Environment overrides::

    QDRANT_URL      default http://127.0.0.1:6333
    OLLAMA_URL      default http://127.0.0.1:11434
    EMBED_MODEL     default mxbai-embed-large
    COLLECTION      default design_systems
    VECTOR_SIZE     default 1024 (must match the embedder output dimension)

The script is stdlib-only (urllib) so it runs on AX102 without extra pip
installs. It drops the collection if it exists and recreates it from scratch,
so every run yields a deterministic state.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

from design_md.cache import DataCache
from design_md.catalog import get_sector
from design_md.parser import DesignMdParser

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "mxbai-embed-large")
COLLECTION = os.environ.get("COLLECTION", "design_systems")
VECTOR_SIZE = int(os.environ.get("VECTOR_SIZE", "1024"))
BATCH = 30
BODY_PAYLOAD_CAP = 5000
# ``mxbai-embed-large`` silently rejects very long inputs with HTTP 500.
# Empirically ~2000 chars (≈512 tokens) stays within the context window and
# keeps enough signal for semantic retrieval. Long sections get a hard cap
# with a retry at an even shorter cap if the first embed call still fails.
EMBED_PRIMARY_CAP = 1800
EMBED_RETRY_CAP = 900


def _request(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    # The URL schemes are controlled by env vars pointing at loopback/LAN
    # services (Qdrant, Ollama) so S310 audit is acceptable here.
    req = urllib.request.Request(  # noqa: S310
        url, data=data, method=method, headers=headers
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


def embed(text: str) -> list[float]:
    """Return the embedding vector for ``text`` via Ollama."""
    resp = _request(
        f"{OLLAMA_URL}/api/embeddings",
        method="POST",
        payload={"model": EMBED_MODEL, "prompt": text},
    )
    return resp["embedding"]


def ensure_collection() -> None:
    """(Re)create the ``design_systems`` collection from scratch."""
    try:
        _request(f"{QDRANT_URL}/collections/{COLLECTION}", method="DELETE")
        print(f"  dropped existing collection {COLLECTION}")
    except urllib.error.HTTPError as err:
        if err.code != 404:
            raise
    _request(
        f"{QDRANT_URL}/collections/{COLLECTION}",
        method="PUT",
        payload={"vectors": {"size": VECTOR_SIZE, "distance": "Cosine"}},
    )
    print(f"  created collection {COLLECTION} (size={VECTOR_SIZE}, distance=Cosine)")


def upsert(points: list[dict]) -> None:
    if not points:
        return
    _request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points",
        method="PUT",
        payload={"points": points},
    )


def main() -> int:
    cache = DataCache()
    parser = DesignMdParser()
    if not cache.is_initialized():
        print("ERROR: submodule not initialised — run git submodule update --init")
        return 2

    ensure_collection()

    batch: list[dict] = []
    point_id = 0
    started = time.time()

    for site, design_path in cache.iter_designs():
        try:
            parsed = parser.parse_file(design_path)
        except OSError as err:
            print(f"  skip {site}: {err}")
            continue
        sector = get_sector(site)
        for section_name, body in parsed["sections"].items():
            body_stripped = body.strip()
            if not body_stripped:
                continue
            header = f"{site} :: {section_name}\n\n"
            primary_text = header + body_stripped[: EMBED_PRIMARY_CAP - len(header)]
            try:
                vector = embed(primary_text)
            except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as err:
                retry_text = header + body_stripped[: EMBED_RETRY_CAP - len(header)]
                try:
                    vector = embed(retry_text)
                except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as err2:
                    print(f"  embed failed {site}/{section_name}: {err} (retry: {err2})")
                    continue
            if len(vector) != VECTOR_SIZE:
                print(f"  WARNING: vector size mismatch {len(vector)} != {VECTOR_SIZE}")
            point_id += 1
            batch.append(
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "site": site,
                        "section": section_name,
                        "sector": sector,
                        "body": body_stripped[:BODY_PAYLOAD_CAP],
                        "body_len": len(body_stripped),
                    },
                }
            )
            if len(batch) >= BATCH:
                upsert(batch)
                print(
                    f"  upserted batch ending at id={point_id} "
                    f"(elapsed={time.time() - started:.1f}s)"
                )
                batch = []

    if batch:
        upsert(batch)
        print(f"  upserted final batch ending at id={point_id}")

    count_resp = _request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/count",
        method="POST",
        payload={"exact": True},
    )
    count = count_resp.get("result", {}).get("count", 0)
    print(f"DONE — {count} points in '{COLLECTION}' (elapsed={time.time() - started:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
