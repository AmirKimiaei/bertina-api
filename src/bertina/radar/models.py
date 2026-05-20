from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RadarItem:
    rank: int
    title: str
    category: str = ""
    subtopic: str = ""
    summary: str = ""
    source: str = ""
    published_at: str = ""
    thumbnail: str = ""
    entities: list[str] = field(default_factory=list)
    news_url: str = ""


@dataclass(slots=True)
class RadarPage:
    hot: list[RadarItem]
    important: list[RadarItem]
    last_updated: str = ""
    _raw_html: str | None = field(default=None, repr=False)
