"""Injected services shared by concrete source adapters."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class SourceRuntime:
    log: Callable[..., None]
    canonicalize_country: Callable[..., str | None]
    safe_float: Callable[[Any], float | None]
    resolve_iso2: Callable[..., str]
    resolve_iso3: Callable[..., str]
    maybe_invert_records: Callable[..., list[dict[str, Any]]]
    save_records: Callable[..., bool]
    save_imf_records: Callable[..., bool]
    keep_or_dummy: Callable[..., None]
    mark_skip: Callable[..., None]
    write_json: Callable[..., None]
    now_utc: Callable[[], str]
    data_dir: Path
    meta_dir: Path
    source_csv_dir: Path
    pending_dir: Path
