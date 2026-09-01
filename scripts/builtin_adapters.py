"""Registration of concrete RealityCheck source adapters."""
from __future__ import annotations

from functools import partial

import requests

from adapters import csv_source, data360, noaa, owid, unhcr, worldbank
from adapters.runtime import SourceRuntime
from fetch_core import AdapterMode, AdapterRegistry, SourceAdapter
from source_contracts import SUPPORTED_SOURCE_TYPES


def build_builtin_adapter_registry(
    runtime: SourceRuntime,
    http_session: requests.Session | None = None,
) -> AdapterRegistry:
    """Build and validate the complete production adapter registry."""
    session = http_session or requests.Session()
    registry = AdapterRegistry()
    registry.register(
        SourceAdapter(
            "worldbank",
            handler=partial(worldbank.run, runtime=runtime, http_get=session.get),
            source_date_resolver=partial(worldbank.resolve_source_date, runtime=runtime, http_get=session.get),
        )
    )
    registry.register(
        SourceAdapter(
            "owid",
            handler=partial(owid.run, runtime=runtime, http_get=session.get),
            source_date_resolver=partial(owid.resolve_source_date, runtime=runtime, http_get=session.get),
        )
    )
    registry.register(
        SourceAdapter("data360", handler=partial(data360.run, runtime=runtime, http_get=session.get))
    )
    registry.register(SourceAdapter("noaa", handler=partial(noaa.run, runtime=runtime, http_get=session.get)))
    registry.register(SourceAdapter("csv", handler=partial(csv_source.run, runtime=runtime)))
    registry.register(SourceAdapter("unhcr", handler=partial(unhcr.run, runtime=runtime, http_get=session.get)))
    registry.register(SourceAdapter("imf", mode=AdapterMode.BATCH))
    registry.register(SourceAdapter("special", mode=AdapterMode.SPECIAL))
    registry.ensure_complete(SUPPORTED_SOURCE_TYPES)
    return registry
