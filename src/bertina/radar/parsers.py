from __future__ import annotations

import logging

from bs4 import BeautifulSoup, Tag

from .._parsers import _safe_select, parse_html
from .models import RadarItem, RadarPage

logger = logging.getLogger("bertina.radar.parsers")


def _parse_card(article: Tag) -> RadarItem | None:
    try:
        rank_span = _safe_select(article, "header span[aria-hidden]")
        rank_text = rank_span.get_text(strip=True) if rank_span else "0"
        # Convert Persian numerals to int
        rank = int(rank_text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))) if rank_text else 0

        category_btn = article.find(attrs={"data-testid": lambda v: v and "radar-card-category-" in v})
        subtopic_a = article.find(attrs={"data-testid": lambda v: v and "radar-card-subtopic-" in v})
        title_h3 = _safe_select(article, "h3")
        summary_p = _safe_select(article, "p.whitespace-pre-line", "p.line-clamp-6")

        # Entities (tag pills)
        entities_ul = article.find(attrs={"data-testid": lambda v: v and "radar-card-entities-" in v})
        entities: list[str] = []
        if entities_ul:
            entities = [a.get_text(strip=True) for a in entities_ul.find_all("a") if a.get_text(strip=True)]

        # Source name
        source_span = article.find(attrs={"data-testid": lambda v: v and "radar-card-source-" in v})
        source = ""
        if source_span:
            font_span = source_span.find("span", class_=lambda c: c and "font-medium" in c)
            source = font_span.get_text(strip=True) if font_span else ""

        # Time
        time_span = article.find(attrs={"data-testid": lambda v: v and "radar-card-time-" in v})

        # Thumbnail
        thumb_a = article.find(attrs={"data-testid": lambda v: v and "radar-card-thumb-" in v})
        thumbnail = ""
        if thumb_a:
            img = thumb_a.find("img")
            thumbnail = img.get("src", "") if img else ""

        # News search URL
        news_a = article.find(attrs={"data-testid": lambda v: v and "radar-card-news-link-" in v})

        if not title_h3:
            return None

        return RadarItem(
            rank=rank,
            title=title_h3.get_text(strip=True),
            category=category_btn.get_text(strip=True) if category_btn else "",
            subtopic=subtopic_a.get_text(strip=True) if subtopic_a else "",
            summary=summary_p.get_text(strip=True) if summary_p else "",
            source=source,
            published_at=time_span.get_text(strip=True) if time_span else "",
            thumbnail=thumbnail,
            entities=entities,
            news_url=news_a.get("href", "") if news_a else "",
        )
    except Exception as exc:
        logger.warning("failed to parse radar card: %s", exc)
        return None


def parse_radar_page(soup: BeautifulSoup) -> RadarPage:
    sections = soup.find_all("section", class_=lambda c: c and "space-y-4" in c)

    hot: list[RadarItem] = []
    important: list[RadarItem] = []

    for section in sections:
        h2 = section.find("h2")
        label = h2.get_text(strip=True) if h2 else ""
        cards = section.find_all("article", attrs={"data-testid": lambda v: v and "radar-card-" in v})
        items = [item for card in cards if (item := _parse_card(card)) is not None]

        if "داغ" in label:
            hot = items
        elif "مهم" in label:
            important = items

    # Last updated timestamp
    last_updated = ""
    for tag in soup.find_all(string=lambda t: t and "آخرین بروزرسانی" in t):
        parent = tag.parent
        gp = parent.parent
        last_updated = gp.get_text(strip=True) if gp else parent.get_text(strip=True)
        last_updated = last_updated.replace("آخرین بروزرسانی:", "").strip()
        break

    return RadarPage(hot=hot, important=important, last_updated=last_updated)
