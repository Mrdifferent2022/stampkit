"""Report (de)serialization."""

from __future__ import annotations

from pathlib import Path

from stampkit.report.schema import Report


def to_json(report: Report, *, indent: int = 2) -> str:
    return report.model_dump_json(indent=indent)


def from_json(payload: str | bytes) -> Report:
    return Report.model_validate_json(payload)


def write_atomic(report: Report, path: str | Path) -> Path:
    """Write report JSON atomically (temp file + rename)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(to_json(report), encoding="utf-8")
    tmp.replace(target)
    return target


def read(path: str | Path) -> Report:
    return from_json(Path(path).read_text(encoding="utf-8"))


def to_dict(report: Report) -> dict[str, object]:
    return report.model_dump(mode="json")
