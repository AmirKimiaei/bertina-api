from __future__ import annotations

import json
import logging
import re

from bs4 import BeautifulSoup, Tag

from .._parsers import _safe_text
from .models import City, PlaceCard, PlaceDetail, PlacesCategory, Province

logger = logging.getLogger("bertina.places")


def parse_provinces(soup: BeautifulSoup) -> list[Province]:
    provinces: list[Province] = []
    for section in soup.select("section.my-8"):
        h2 = section.select_one("h2")
        if not h2:
            continue
        prov_name = h2.get_text(strip=True)
        cities: list[City] = []
        for card in section.select("a.rounded-xl.border"):
            href = card.get("href", "")
            name_tag = card.select_one("div.font-semibold")
            count_tag = card.select_one("div.text-xs")
            cat_tags = card.select("span.rounded-full")
            if not name_tag:
                continue
            cities.append(City(
                name=name_tag.get_text(strip=True),
                url=str(href),
                place_count=count_tag.get_text(strip=True) if count_tag else "",
                categories=[t.get_text(strip=True) for t in cat_tags],
            ))
        provinces.append(Province(name=prov_name, cities=cities))
    return provinces


def parse_city_categories(soup: BeautifulSoup) -> list[PlacesCategory]:
    categories: list[PlacesCategory] = []
    for card in soup.select("a.rounded-xl.border"):
        href = card.get("href", "")
        name_tag = card.select_one("div.font-semibold")
        count_tag = card.select_one("div.text-xs")
        if not name_tag:
            continue
        categories.append(PlacesCategory(
            name=name_tag.get_text(strip=True),
            url=str(href),
            place_count=count_tag.get_text(strip=True) if count_tag else "",
        ))
    return categories


def parse_place_cards(soup: BeautifulSoup) -> list[PlaceCard]:
    cards: list[PlaceCard] = []
    for card in soup.select("a.group.flex.flex-col.rounded-2xl.border"):
        href = str(card.get("href", ""))
        slug = href.rstrip("/").rsplit("/", 1)[-1] if href else ""
        name_tag = card.select_one("h3.font-semibold")
        if not name_tag:
            continue
        neigh_tag = card.select_one("p.mt-1.text-xs")
        rating_tag = card.select_one("span.font-semibold")
        img_tag = card.select_one("img")
        cards.append(PlaceCard(
            name=name_tag.get_text(strip=True),
            url=href,
            slug=slug,
            neighbourhood=neigh_tag.get_text(strip=True) if neigh_tag else "",
            rating=rating_tag.get_text(strip=True) if rating_tag else "",
            thumbnail=str(img_tag.get("src", "")) if img_tag else "",
        ))
    return cards


def _extract_place_json(html: str) -> dict | None:
    """Extract place data from Next.js flight payload in script tags."""
    # The JSON is escaped inside a JS string: \"slug\":\"value\",\"title_fa\"
    pattern = re.compile(r'\\"slug\\":\\"[^"\\]+\\",\s*\\"title_fa\\"')
    match = pattern.search(html)
    if not match:
        return None
    start = html.rfind("{", 0, match.start())
    if start == -1:
        return None
    chunk = html[start:start + 8192].replace('\\"', '"')
    depth = 0
    end = 0
    for i, ch in enumerate(chunk):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if not end:
        return None
    try:
        return json.loads(chunk[:end])
    except json.JSONDecodeError as exc:
        logger.debug("place JSON parse failed: %s", exc)
        return None


def parse_place_detail(soup: BeautifulSoup, html: str, debug: bool = False) -> PlaceDetail:
    data = _extract_place_json(html)
    if data:
        hours = data.get("opening_hours") or {}
        return PlaceDetail(
            name=data.get("title_fa", ""),
            slug=data.get("slug", ""),
            city=data.get("city_fa", ""),
            neighbourhood=data.get("neighbourhood_fa", ""),
            description=data.get("description_fa", ""),
            address=data.get("address", ""),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            rating=data.get("rating"),
            rating_count=data.get("rating_count", 0) or 0,
            category=data.get("type", ""),
            phone=data.get("phone_number") or "",
            website=data.get("website") or "",
            opening_hours=hours if isinstance(hours, dict) else {},
            thumbnail=data.get("thumbnail_url", ""),
            _raw_html=html if debug else None,
        )
    # Fallback: extract what we can from rendered HTML
    h1 = soup.select_one("h1")
    name = h1.get_text(strip=True) if h1 else ""
    slug_tag = soup.select_one("link[rel='canonical']")
    slug = ""
    if slug_tag:
        href = slug_tag.get("href", "")
        slug = str(href).rstrip("/").rsplit("/", 1)[-1]
    logger.warning("place detail JSON not found, using HTML fallback for %r", slug)
    return PlaceDetail(
        name=name,
        slug=slug,
        _raw_html=html if debug else None,
    )
