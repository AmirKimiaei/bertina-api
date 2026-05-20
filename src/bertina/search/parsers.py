from __future__ import annotations

import base64
import logging
import re
from urllib.parse import parse_qs, urlencode, urlparse

from bs4 import BeautifulSoup, Tag

from .._parsers import _safe_attr, _safe_select, _safe_text, parse_html
from .models import (
    ImageResult,
    NewsResult,
    PlaceResult,
    ScholarResult,
    ShoppingResult,
    VideoResult,
    WebResult,
)

logger = logging.getLogger("bertina.search.parsers")


def _decode_click_url(href: str) -> str:
    """Extract the real destination URL from Bertina's /api/click?dest=<b64> links."""
    if not href or not href.startswith("/api/click"):
        return href
    try:
        qs = parse_qs(urlparse(href).query)
        dest = qs.get("dest", [""])[0]
        if dest:
            return base64.urlsafe_b64decode(dest + "==").decode("utf-8", errors="replace")
    except Exception:
        pass
    return href


def parse_web_results(soup: BeautifulSoup) -> list[WebResult]:
    results = []
    for article in soup.find_all("article", class_=lambda c: c and "animate-fade-in" in c and "pb-6" in c):
        cite = _safe_select(article, "cite")
        title_a = _safe_select(article, "h3 > a", "h3 a")
        desc = _safe_select(article, "p.leading-relaxed", "p.line-clamp-3")
        favicon = _safe_select(article, 'img[height="16"]')

        if not title_a:
            continue

        url = _decode_click_url(title_a.get("href", ""))
        if not url and cite:
            url = cite.get("title", cite.get_text(strip=True))

        sitelinks = []
        for a in article.select("div.mt-3 a"):
            sitelinks.append({"text": a.get_text(strip=True), "url": a.get("href", "")})

        results.append(WebResult(
            title=title_a.get_text(strip=True),
            url=url,
            description=desc.get_text(strip=True) if desc else "",
            favicon_url=favicon.get("src", "") if favicon else "",
            sitelinks=sitelinks,
        ))
    return results


def parse_news_results(soup: BeautifulSoup) -> list[NewsResult]:
    results = []
    for article in soup.find_all("article", class_="h-full"):
        link = _safe_select(article, "a[aria-label]", "a[href]")
        if not link:
            continue

        title_p = _safe_select(article, "p.line-clamp-2", "p.font-semibold")
        source = _safe_select(article, "span.truncate")
        time_span = _safe_select(article, "span.shrink-0")
        thumbnail = _safe_select(article, "img.object-cover", "img")

        results.append(NewsResult(
            title=link.get("aria-label", "") or (title_p.get_text(strip=True) if title_p else ""),
            url=link.get("href", ""),
            source=source.get_text(strip=True) if source else "",
            published_at=time_span.get_text(strip=True) if time_span else "",
            thumbnail=thumbnail.get("src", "") if thumbnail else "",
        ))
    return results


def parse_shopping_results(soup: BeautifulSoup) -> list[ShoppingResult]:
    results = []
    for li in soup.find_all("li", attrs={"data-testid": "shopping-card"}):
        title_a = _safe_select(li, "a.font-bold", "a.text-base")
        desc = _safe_select(li, "p.line-clamp-3", "p.mt-2")
        buy_a = _safe_select(li, "a.bg-\\[var\\(--brand-orange\\)\\]", "a[href*='torob']", "a[href*='emalls']")
        merchant_name = _safe_select(li, "span.font-medium")
        merchant_domain_tag = li.find("span", class_=lambda c: not c or "font-medium" not in " ".join(c if c else []))

        # merchant domain is the plain <span> after the bullet separator
        spans = li.select("div.mb-2 span")
        merchant_domain = ""
        for span in spans:
            text = span.get_text(strip=True)
            if "." in text and len(text) < 40:
                merchant_domain = text
                break

        if not title_a:
            continue

        results.append(ShoppingResult(
            title=title_a.get_text(strip=True),
            url=title_a.get("href", ""),
            description=desc.get_text(strip=True) if desc else "",
            merchant=merchant_name.get_text(strip=True) if merchant_name else "",
            merchant_domain=merchant_domain,
            buy_url=buy_a.get("href", "") if buy_a else "",
        ))
    return results


def parse_place_results(soup: BeautifulSoup) -> list[PlaceResult]:
    results = []
    for card in soup.find_all(attrs={"data-testid": "place-card"}):
        name_tag = _safe_select(card, "h3", "h2", ".place-name")
        link = _safe_select(card, "a[href]")
        results.append(PlaceResult(
            name=name_tag.get_text(strip=True) if name_tag else "",
            url=link.get("href", "") if link else "",
        ))
    return results


def parse_image_results(soup: BeautifulSoup) -> list[ImageResult]:
    results = []
    for article in soup.find_all("article", attrs={"role": "button"}):
        label = article.get("aria-label", "")
        thumbnail = _safe_select(article, "img.absolute", "img")
        source_p = article.select("div.p-2 p")

        title = label.split(" - ")[0] if " - " in label else label
        source = source_p[1].get_text(strip=True) if len(source_p) > 1 else ""

        results.append(ImageResult(
            title=title,
            thumbnail=thumbnail.get("src", "") if thumbnail else "",
            source=source,
        ))
    return results


def parse_video_results(soup: BeautifulSoup) -> list[VideoResult]:
    results = []
    for article in soup.find_all("article", attrs={"role": "button"}):
        label = article.get("aria-label", "")
        thumbnail = _safe_select(article, "img.absolute", "img")
        source_p = article.select("div.p-2 p")

        title = label.split(" - ")[0] if " - " in label else label
        source = source_p[1].get_text(strip=True) if len(source_p) > 1 else ""

        results.append(VideoResult(
            title=title,
            thumbnail=thumbnail.get("src", "") if thumbnail else "",
            source=source,
        ))
    return results


def parse_scholar_results(soup: BeautifulSoup) -> list[ScholarResult]:
    results = []
    for article in soup.find_all("article", class_=lambda c: c and "animate-fade-in" in c and "pb-6" in c):
        title_a = _safe_select(article, "h3 > a", "h3 a")
        meta = _safe_select(article, "div.mt-1.text-sm", "div.line-clamp-1")
        desc = _safe_select(article, "p.mt-2", "p.leading-relaxed")

        # citations: span containing 'ارجاع'
        citations = ""
        year = ""
        for span in article.find_all("span"):
            text = span.get_text(strip=True)
            if "ارجاع" in text:
                citations = re.sub(r"[^\d]", "", text)
            elif re.fullmatch(r"\d{4}", text):
                year = text

        is_pdf = bool(article.find("a", attrs={"title": "PDF"}))

        if not title_a:
            continue

        url = title_a.get("href", "")
        results.append(ScholarResult(
            title=title_a.get_text(strip=True),
            url=url,
            authors_and_year=meta.get_text(strip=True) if meta else "",
            citations=citations,
            year=year,
            description=desc.get_text(strip=True) if desc else "",
            is_pdf=is_pdf,
        ))
    return results


def parse_pagination(soup: BeautifulSoup) -> list[int]:
    """Return list of available page numbers from the pagination nav."""
    nav = soup.find("nav", attrs={"aria-label": lambda v: v and "صفحه" in v})
    if not nav:
        return []
    pages = []
    for a in nav.find_all("a", attrs={"aria-label": True}):
        label = a.get("aria-label", "")
        nums = re.findall(r"\d+", label)
        if nums:
            pages.append(int(nums[0]))
    return sorted(set(pages))
