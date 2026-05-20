from __future__ import annotations

import logging
from typing import Any

from .._base import AsyncBaseClient, BaseClient
from ..constants import SEARCH_BASE
from .._parsers import parse_html
from .parsers import parse_radar_page
from .models import RadarPage

logger = logging.getLogger("bertina.radar")

_RADAR_URL = f"{SEARCH_BASE}/radar"
_DEFAULT_TTL = 900  # 15 minutes


class BertinaRadar(BaseClient):
    """Synchronous Bertina news radar client."""

    def __init__(self, *, cache_ttl: int = _DEFAULT_TTL, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl, **kwargs)

    def get(self) -> RadarPage:
        logger.debug("fetching radar page")
        html = self._get(_RADAR_URL)
        soup = parse_html(html)
        page = parse_radar_page(soup)
        if self.debug:
            object.__setattr__(page, "_raw_html", html)
        return page


class AsyncBertinaRadar(AsyncBaseClient):
    """Asynchronous Bertina news radar client."""

    def __init__(self, *, cache_ttl: int = _DEFAULT_TTL, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl, **kwargs)

    async def get(self) -> RadarPage:
        logger.debug("fetching radar page")
        html = await self._aget(_RADAR_URL)
        soup = parse_html(html)
        page = parse_radar_page(soup)
        if self.debug:
            object.__setattr__(page, "_raw_html", html)
        return page
