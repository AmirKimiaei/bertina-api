from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import SearchType


@dataclass(slots=True)
class WebResult:
    title: str
    url: str
    description: str = ""
    favicon_url: str = ""
    sitelinks: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class NewsResult:
    title: str
    url: str
    source: str = ""
    published_at: str = ""
    thumbnail: str = ""


@dataclass(slots=True)
class ShoppingResult:
    title: str
    url: str
    description: str = ""
    merchant: str = ""
    merchant_domain: str = ""
    buy_url: str = ""


@dataclass(slots=True)
class PlaceResult:
    name: str
    url: str = ""
    category: str = ""
    rating: str = ""
    review_count: str = ""
    is_open: bool = False
    hours: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""


@dataclass(slots=True)
class ImageResult:
    title: str
    thumbnail: str
    source: str = ""


@dataclass(slots=True)
class VideoResult:
    title: str
    thumbnail: str
    source: str = ""


@dataclass(slots=True)
class ScholarResult:
    title: str
    url: str
    authors_and_year: str = ""
    citations: str = ""
    year: str = ""
    description: str = ""
    is_pdf: bool = False


@dataclass(slots=True)
class SearchResponse:
    query: str
    page: int
    search_type: SearchType
    results: list[Any]
    related: list[str] = field(default_factory=list)
    _raw_html: str | None = field(default=None, repr=False)
