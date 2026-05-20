from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class City:
    name: str
    url: str
    place_count: str = ""
    categories: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Province:
    name: str
    cities: list[City] = field(default_factory=list)


@dataclass(slots=True)
class PlacesCategory:
    name: str
    url: str
    place_count: str = ""


@dataclass(slots=True)
class PlaceCard:
    name: str
    url: str
    slug: str = ""
    neighbourhood: str = ""
    rating: str = ""
    thumbnail: str = ""


@dataclass(slots=True)
class PlaceDetail:
    name: str
    slug: str
    city: str = ""
    neighbourhood: str = ""
    description: str = ""
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    rating: float | None = None
    rating_count: int = 0
    category: str = ""
    phone: str = ""
    website: str = ""
    opening_hours: dict[str, str] = field(default_factory=dict)
    thumbnail: str = ""
    _raw_html: str | None = field(default=None, repr=False)
