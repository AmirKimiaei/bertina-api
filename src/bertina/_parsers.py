from __future__ import annotations

import logging

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger("bertina.parsers")


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _safe_select(tag: Tag | BeautifulSoup, *selectors: str) -> Tag | None:
    """Try CSS selectors in order, return the first match or None."""
    for sel in selectors:
        try:
            result = tag.select_one(sel)
            if result:
                return result
        except Exception:
            continue
    return None


def _safe_text(tag: Tag | BeautifulSoup, *selectors: str, default: str = "") -> str:
    el = _safe_select(tag, *selectors)
    if el:
        return el.get_text(strip=True)
    return default


def _safe_attr(
    tag: Tag | BeautifulSoup, attr: str, *selectors: str, default: str = ""
) -> str:
    el = _safe_select(tag, *selectors)
    if el:
        val = el.get(attr, default)
        return str(val) if val else default
    return default
