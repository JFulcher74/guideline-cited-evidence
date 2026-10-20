"""Read the iCite JSONL cache from the plain file or its committed .gz copy."""
import gzip
import json
from pathlib import Path


def gz_path(path: Path) -> Path:
    return path.with_name(path.name + ".gz")


def cache_exists(path: Path) -> bool:
    return path.exists() or gz_path(path).exists()


def read_jsonl(path: Path) -> list:
    """Rows from `path`, falling back to `path`.gz (the copy kept in git)."""
    if path.exists():
        with path.open() as fh:
            return [json.loads(line) for line in fh]
    with gzip.open(gz_path(path), "rt") as fh:
        return [json.loads(line) for line in fh]


def write_gz_copy(path: Path) -> None:
    with path.open("rb") as src, gzip.open(gz_path(path), "wb", compresslevel=9) as dst:
        dst.write(src.read())
