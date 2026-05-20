from __future__ import annotations

import logging
from typing import Any

from .._base import AsyncBaseClient, BaseClient
from ..constants import SEARCH_BASE
from ..exceptions import BertinaParseError
from .parsers import (
    parse_image_results,
    parse_news_results,
    parse_place_results,
    parse_scholar_results,
    parse_shopping_results,
    parse_video_results,
    parse_web_results,
)
from .._parsers import parse_html
from .enums import SearchType
from .models import SearchResponse

logger = logging.getLogger("bertina.search")

_REGISTRY = {
    SearchType.WEB:      parse_web_results,
    SearchType.NEWS:     parse_news_results,
    SearchType.SHOPPING: parse_shopping_results,
    SearchType.PLACES:   parse_place_results,
    SearchType.IMAGES:   parse_image_results,
    SearchType.VIDEOS:   parse_video_results,
    SearchType.SCHOLAR:  parse_scholar_results,
}

# Per-type cache TTL overrides (seconds)
_TTL = {
    SearchType.WEB:      300,
    SearchType.NEWS:     300,
    SearchType.SHOPPING: 300,
    SearchType.IMAGES:   300,
    SearchType.VIDEOS:   300,
    SearchType.PLACES:   3600,
    SearchType.SCHOLAR:  3600,
}


def _build_params(query: str, search_type: SearchType, page: int) -> dict:
    params: dict[str, Any] = {"q": query}
    type_param = search_type.to_param()
    if type_param:
        params["type"] = type_param
    if page > 1:
        params["page"] = page
    return params


def _parse_response(html: str, query: str, search_type: SearchType, page: int, debug: bool) -> SearchResponse:
    soup = parse_html(html)
    parser = _REGISTRY.get(search_type, parse_web_results)
    try:
        results = parser(soup)
    except Exception as exc:
        logger.warning("parser failed for %s: %s", search_type, exc)
        raise BertinaParseError(str(exc)) from exc

    return SearchResponse(
        query=query,
        page=page,
        search_type=search_type,
        results=results,
        _raw_html=html if debug else None,
    )


class BertinaSearch(BaseClient):
    """Synchronous Bertina search client."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or 300, **kwargs)

    def search(
        self,
        query: str,
        *,
        type: SearchType = SearchType.WEB,
        page: int = 1,
    ) -> SearchResponse:
        params = _build_params(query, type, page)
        url = f"{SEARCH_BASE}/search"
        logger.debug("search query=%r type=%s page=%d", query, type, page)
        html = self._get(url, params)
        return _parse_response(html, query, type, page, self.debug)


class AsyncBertinaSearch(AsyncBaseClient):
    """Asynchronous Bertina search client."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or 300, **kwargs)

    async def search(
        self,
        query: str,
        *,
        type: SearchType = SearchType.WEB,
        page: int = 1,
    ) -> SearchResponse:
        params = _build_params(query, type, page)
        url = f"{SEARCH_BASE}/search"
        logger.debug("search query=%r type=%s page=%d", query, type, page)
        html = await self._aget(url, params)
        return _parse_response(html, query, type, page, self.debug)
