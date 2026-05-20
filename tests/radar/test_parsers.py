from __future__ import annotations

import pytest

from bertina._parsers import parse_html
from bertina.radar.models import RadarItem, RadarPage
from bertina.radar.parsers import parse_radar_page
from tests.conftest import load_fixture


@pytest.fixture
def radar_soup():
    return parse_html(load_fixture("radar", "radar.html"))


class TestRadarParser:
    def test_returns_radar_page(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert isinstance(page, RadarPage)

    def test_hot_items_non_empty(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert len(page.hot) > 0

    def test_important_items_non_empty(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert len(page.important) > 0

    def test_hot_item_type(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert all(isinstance(item, RadarItem) for item in page.hot)

    def test_important_item_type(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert all(isinstance(item, RadarItem) for item in page.important)

    def test_hot_items_have_title(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert all(item.title for item in page.hot)

    def test_hot_items_have_rank(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert all(item.rank > 0 for item in page.hot)

    def test_hot_ranks_sequential(self, radar_soup):
        page = parse_radar_page(radar_soup)
        ranks = [item.rank for item in page.hot]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_important_items_have_title(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert all(item.title for item in page.important)

    def test_entities_are_list(self, radar_soup):
        page = parse_radar_page(radar_soup)
        assert all(isinstance(item.entities, list) for item in page.hot)
