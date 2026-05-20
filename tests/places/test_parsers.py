from __future__ import annotations

import pytest

from bertina._parsers import parse_html
from bertina.places.models import City, PlaceCard, PlaceDetail, PlacesCategory, Province
from bertina.places.parsers import (
    parse_city_categories,
    parse_place_cards,
    parse_place_detail,
    parse_provinces,
)
from tests.conftest import load_fixture


@pytest.fixture
def provinces_soup():
    return parse_html(load_fixture("places", "provinces.html"))


@pytest.fixture
def city_soup():
    return parse_html(load_fixture("places", "city.html"))


@pytest.fixture
def category_soup():
    return parse_html(load_fixture("places", "category.html"))


@pytest.fixture
def detail_data():
    html = load_fixture("places", "detail.html")
    soup = parse_html(html)
    return soup, html


class TestProvincesParser:
    def test_returns_32_provinces(self, provinces_soup):
        provinces = parse_provinces(provinces_soup)
        assert len(provinces) == 32

    def test_province_type(self, provinces_soup):
        provinces = parse_provinces(provinces_soup)
        assert all(isinstance(p, Province) for p in provinces)

    def test_province_has_name(self, provinces_soup):
        provinces = parse_provinces(provinces_soup)
        assert all(p.name for p in provinces)

    def test_provinces_have_cities(self, provinces_soup):
        provinces = parse_provinces(provinces_soup)
        assert all(len(p.cities) > 0 for p in provinces)

    def test_city_type(self, provinces_soup):
        provinces = parse_provinces(provinces_soup)
        for p in provinces:
            assert all(isinstance(c, City) for c in p.cities)

    def test_city_has_name_and_url(self, provinces_soup):
        provinces = parse_provinces(provinces_soup)
        for p in provinces:
            for c in p.cities:
                assert c.name
                assert c.url.startswith("http")

    def test_total_cities(self, provinces_soup):
        provinces = parse_provinces(provinces_soup)
        total = sum(len(p.cities) for p in provinces)
        assert total == 1014


class TestCityCategoriesParser:
    def test_returns_categories(self, city_soup):
        cats = parse_city_categories(city_soup)
        assert len(cats) > 0

    def test_category_type(self, city_soup):
        cats = parse_city_categories(city_soup)
        assert all(isinstance(c, PlacesCategory) for c in cats)

    def test_category_has_name_and_url(self, city_soup):
        cats = parse_city_categories(city_soup)
        assert all(c.name for c in cats)
        assert all(c.url for c in cats)


class TestPlaceCardsParser:
    def test_returns_cards(self, category_soup):
        cards = parse_place_cards(category_soup)
        assert len(cards) > 0

    def test_card_type(self, category_soup):
        cards = parse_place_cards(category_soup)
        assert all(isinstance(c, PlaceCard) for c in cards)

    def test_card_has_name_and_url(self, category_soup):
        cards = parse_place_cards(category_soup)
        assert all(c.name for c in cards)
        assert all(c.url for c in cards)

    def test_slug_extracted_from_url(self, category_soup):
        cards = parse_place_cards(category_soup)
        assert all(c.slug for c in cards)


class TestPlaceDetailParser:
    def test_returns_place_detail(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert isinstance(detail, PlaceDetail)

    def test_name_parsed(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert detail.name == "Hilo cafe"

    def test_slug_parsed(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert detail.slug == "hilo-cafe"

    def test_city_parsed(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert detail.city == "تهران"

    def test_neighbourhood_parsed(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert detail.neighbourhood == "دربند"

    def test_coordinates_parsed(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert detail.latitude == pytest.approx(35.8147, abs=0.001)
        assert detail.longitude == pytest.approx(51.4319, abs=0.001)

    def test_rating_parsed(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert detail.rating == 5
        assert detail.rating_count == 10

    def test_opening_hours_parsed(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html)
        assert len(detail.opening_hours) == 7

    def test_no_raw_html_by_default(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html, debug=False)
        assert detail._raw_html is None

    def test_raw_html_in_debug_mode(self, detail_data):
        soup, html = detail_data
        detail = parse_place_detail(soup, html, debug=True)
        assert detail._raw_html is not None
