"""Source-scan guard: the source tree must not reference external publications."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

# Word-boundary regexes; short/common fragments (e.g. "horizon" inside
# "horizontal") must not produce false positives.
FORBIDDEN_PATTERNS = [
    r"\bcirp\b",
    r"\bprocedia\b",
    r"\bterzakis\b",
    r"\bgerontas\b",
    r"\bsouflas\b",
    r"\bstavropoulos\b",
    r"\bpatras\b",
    r"\bdoi\b",
    r"\belsevier\b",
    r"\bsciencedirect\b",
    r"\bhorizon\s+europe\b",
    r"\br3group\b",
    r"\bautoform\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_PATTERNS]


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
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern, rx in zip(FORBIDDEN_PATTERNS, _COMPILED, strict=True):
            if rx.search(text):
                hits.append(f"{path}: contains {pattern!r}")
    assert not hits, "publication references found:\n" + "\n".join(hits)
