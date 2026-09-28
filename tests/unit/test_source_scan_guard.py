"""Source-scan guard: the source tree must not reference external publications."""

from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

FORBIDDEN_TERMS = [
    "cirp",
    "procedia",
    "terzakis",
    "stavropoulos",
    "patras",
    "doi",
    "elsevier",
    "sciencedirect",
    "horizon",
    "r3group",
]


def _source_files():
    exts = {".py", ".yaml", ".yml", ".toml", ".md"}
    root = Path(__file__).resolve().parents[2]
    for sub in ("src", "addons", "rules_custom", "scripts"):
        d = root / sub
        if d.exists():
            for p in sorted(d.rglob("*")):
                if p.suffix.lower() in exts:
                    yield p


def test_no_publication_references_in_source():
    hits: list[str] = []
    for path in _source_files():
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in FORBIDDEN_TERMS:
            if term in text:
                hits.append(f"{path}: contains {term!r}")
    assert not hits, "publication references found:\n" + "\n".join(hits)
