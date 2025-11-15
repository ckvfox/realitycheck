"""Shared helpers for RealityCheck command-line scripts."""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def ensure_utf8_stdout() -> None:
    """Force UTF-8 encoding for stdout if possible."""
    if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")


def utc_now_iso(timespec: str = "seconds") -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat(timespec=timespec).replace("+00:00", "Z")


def setup_logger(name: str, log_file: Path, *, level: int = logging.INFO) -> logging.Logger:
    """Return a logger that writes to stdout and the provided file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("[%(asctime)s UTC] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def _write_atomic(path: Path, content: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)


def safe_write_text(path: Path, content: str, *, logger: Optional[logging.Logger] = None, note: str = "") -> None:
    """Safely write UTF-8 text to ``path`` using an atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic(path, content or "")
    if logger:
        logger.info(note or f"Text written → {path}")


def safe_write_json(path: Path, data: Any, *, logger: Optional[logging.Logger] = None, note: str = "") -> None:
    """Safely write JSON data to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    _write_atomic(path, serialized)
    if logger:
        logger.info(note or f"JSON written → {path}")


def read_json(path: Path, default: Any = None, *, logger: Optional[logging.Logger] = None) -> Any:
    """Read JSON content returning ``default`` on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        if logger:
            logger.warning("Could not read %s: %s", path, exc)
        return default
