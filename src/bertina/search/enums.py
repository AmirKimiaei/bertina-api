from __future__ import annotations

from enum import Enum


class SearchType(str, Enum):
    WEB = "web"
    NEWS = "news"
    SHOPPING = "shopping"
    PLACES = "places"
    IMAGES = "images"
    VIDEOS = "video"
    SCHOLAR = "scholar"

    def to_param(self) -> str | None:
        """Return the ?type= query param value, or None for WEB (default)."""
        return None if self is SearchType.WEB else self.value
