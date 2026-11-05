"""Injected services shared by concrete source adapters."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


def normalize_country_key(value: str) -> str:
    normalized = "".join(
        char for char in unicodedata.normalize("NFKD", str(value).lower())
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "", normalized)


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
    save_region_records: Callable[..., bool]
    keep_or_dummy: Callable[..., None]
    mark_skip: Callable[..., None]
    write_json: Callable[..., None]
    now_utc: Callable[[], str]
    data_dir: Path
    meta_dir: Path
    source_csv_dir: Path
    region_source_csv_dir: Path
    pending_dir: Path
