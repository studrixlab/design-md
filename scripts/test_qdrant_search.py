#!/usr/bin/env python3
"""Quick smoke test: semantic search over the ``design_systems`` Qdrant collection.

Run on AX102 where both Ollama (11434) and Qdrant (6333) are local.
Prints the top-3 hits for each of a handful of hand-crafted queries, so you
can eyeball whether the embeddings actually retrieve the right design systems.
"""

from __future__ import annotations

import json
import os
import urllib.request

QDRANT = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("EMBED_MODEL", "mxbai-embed-large")
COLLECTION = os.environ.get("COLLECTION", "design_systems")


def embed(text: str) -> list[float]:
    payload = {"model": MODEL, "prompt": text}
    req = urllib.request.Request(  # noqa: S310
        f"{OLLAMA}/api/embeddings",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.loads(resp.read())["embedding"]


def search(query: str, limit: int = 3) -> list[dict]:
    vec = embed(query)
    payload = {"vector": vec, "limit": limit, "with_payload": True}
    req = urllib.request.Request(  # noqa: S310
        f"{QDRANT}/collections/{COLLECTION}/points/search",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.loads(resp.read())["result"]


QUERIES = [
    "warm earthy terracotta brand color not tech",
    "subtle glassmorphism hover with backdrop blur",
    "aggressive saturated gradient for hero backgrounds",
    "monochrome minimal black and white editorial type",
    "bold saturated playful rounded buttons",
]


def main() -> int:
    for query in QUERIES:
        print(f"\n=== {query} ===")
        for hit in search(query, 3):
            payload = hit["payload"]
            score = hit["score"]
            site = payload["site"]
            section = payload["section"][:45]
            print(f"  {score:.3f}  {site:<14}  {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
