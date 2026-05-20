from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from .._base import AsyncBaseClient, BaseClient
from .._parsers import parse_html
from ..constants import SEARCH_BASE
from ..exceptions import BertinaParseError
from .models import PlaceCard, PlaceDetail, PlacesCategory, Province
from .parsers import (
    parse_city_categories,
    parse_place_cards,
    parse_place_detail,
    parse_provinces,
)

logger = logging.getLogger("bertina.places")

_PROVINCES_TTL = 86400   # 24 h — province/city list rarely changes
_CATEGORY_TTL = 3600
_LISTING_TTL = 1800
_DETAIL_TTL = 3600


class BertinaPlaces(BaseClient):
    """Synchronous Bertina places client."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or _PROVINCES_TTL, **kwargs)

    def get_provinces(self) -> list[Province]:
        url = f"{SEARCH_BASE}/places"
        html = self._get(url)
        soup = parse_html(html)
        try:
            return parse_provinces(soup)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc

    def get_city(self, city: str) -> list[PlacesCategory]:
        """Return categories available in a city (e.g. city='تهران')."""
        url = f"{SEARCH_BASE}/places/{quote(city, safe='')}"
        html = self._get(url)
        soup = parse_html(html)
        try:
            return parse_city_categories(soup)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc

    def get_category(self, city: str, category: str) -> list[PlaceCard]:
        """Return place cards for a city/category combination."""
        url = f"{SEARCH_BASE}/places/{quote(city, safe='')}/{quote(category, safe='')}"
        html = self._get(url)
        soup = parse_html(html)
        try:
            return parse_place_cards(soup)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc

    def get_place(self, slug: str) -> PlaceDetail:
        """Return full detail for a place by its slug."""
        url = f"{SEARCH_BASE}/place/{slug}"
        html = self._get(url)
        soup = parse_html(html)
        try:
            return parse_place_detail(soup, html, self.debug)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc


class AsyncBertinaPlaces(AsyncBaseClient):
    """Asynchronous Bertina places client."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or _PROVINCES_TTL, **kwargs)

    async def get_provinces(self) -> list[Province]:
        url = f"{SEARCH_BASE}/places"
        html = await self._aget(url)
        soup = parse_html(html)
        try:
            return parse_provinces(soup)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc

    async def get_city(self, city: str) -> list[PlacesCategory]:
        url = f"{SEARCH_BASE}/places/{quote(city, safe='')}"
        html = await self._aget(url)
        soup = parse_html(html)
        try:
            return parse_city_categories(soup)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc

    async def get_category(self, city: str, category: str) -> list[PlaceCard]:
        url = f"{SEARCH_BASE}/places/{quote(city, safe='')}/{quote(category, safe='')}"
        html = await self._aget(url)
        soup = parse_html(html)
        try:
            return parse_place_cards(soup)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc

    async def get_place(self, slug: str) -> PlaceDetail:
        url = f"{SEARCH_BASE}/place/{slug}"
        html = await self._aget(url)
        soup = parse_html(html)
        try:
            return parse_place_detail(soup, html, self.debug)
        except Exception as exc:
            raise BertinaParseError(str(exc)) from exc
