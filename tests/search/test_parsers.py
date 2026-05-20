from __future__ import annotations

import pytest

from bertina._parsers import parse_html
from bertina.search.parsers import (
    parse_image_results,
    parse_news_results,
    parse_place_results,
    parse_scholar_results,
    parse_shopping_results,
    parse_video_results,
    parse_web_results,
)
from bertina.search.models import (
    ImageResult,
    NewsResult,
    PlaceResult,
    ScholarResult,
    ShoppingResult,
    VideoResult,
    WebResult,
)
from tests.conftest import load_fixture


@pytest.fixture
def web_soup():
    return parse_html(load_fixture("search", "web.html"))


@pytest.fixture
def news_soup():
    return parse_html(load_fixture("search", "news.html"))


@pytest.fixture
def shopping_soup():
    return parse_html(load_fixture("search", "shopping.html"))


@pytest.fixture
def places_soup():
    return parse_html(load_fixture("search", "places.html"))


@pytest.fixture
def images_soup():
    return parse_html(load_fixture("search", "images.html"))


@pytest.fixture
def videos_soup():
    return parse_html(load_fixture("search", "videos.html"))


@pytest.fixture
def scholar_soup():
    return parse_html(load_fixture("search", "scholar.html"))


class TestWebParser:
    def test_returns_results(self, web_soup):
        results = parse_web_results(web_soup)
        assert len(results) > 0

    def test_result_type(self, web_soup):
        results = parse_web_results(web_soup)
        assert all(isinstance(r, WebResult) for r in results)

    def test_title_non_empty(self, web_soup):
        results = parse_web_results(web_soup)
        assert all(r.title for r in results)

    def test_url_non_empty(self, web_soup):
        results = parse_web_results(web_soup)
        assert all(r.url for r in results)

    def test_url_is_real_not_click_tracker(self, web_soup):
        results = parse_web_results(web_soup)
        for r in results:
            assert "/api/click" not in r.url
            assert r.url.startswith("http")

    def test_is_alive_defaults_none(self, web_soup):
        results = parse_web_results(web_soup)
        assert all(r.is_alive is None for r in results)


class TestNewsParser:
    def test_returns_results(self, news_soup):
        results = parse_news_results(news_soup)
        assert len(results) > 0

    def test_result_type(self, news_soup):
        results = parse_news_results(news_soup)
        assert all(isinstance(r, NewsResult) for r in results)

    def test_title_non_empty(self, news_soup):
        results = parse_news_results(news_soup)
        assert all(r.title for r in results)

    def test_url_non_empty(self, news_soup):
        results = parse_news_results(news_soup)
        assert all(r.url for r in results)


class TestShoppingParser:
    def test_returns_results(self, shopping_soup):
        results = parse_shopping_results(shopping_soup)
        assert len(results) > 0

    def test_result_type(self, shopping_soup):
        results = parse_shopping_results(shopping_soup)
        assert all(isinstance(r, ShoppingResult) for r in results)

    def test_title_non_empty(self, shopping_soup):
        results = parse_shopping_results(shopping_soup)
        assert all(r.title for r in results)


class TestPlacesSearchParser:
    def test_returns_list(self, places_soup):
        results = parse_place_results(places_soup)
        assert isinstance(results, list)

    def test_result_type(self, places_soup):
        results = parse_place_results(places_soup)
        assert all(isinstance(r, PlaceResult) for r in results)


class TestImagesParser:
    def test_returns_results(self, images_soup):
        results = parse_image_results(images_soup)
        assert len(results) > 0

    def test_result_type(self, images_soup):
        results = parse_image_results(images_soup)
        assert all(isinstance(r, ImageResult) for r in results)

    def test_title_non_empty(self, images_soup):
        results = parse_image_results(images_soup)
        assert all(r.title for r in results)


class TestVideosParser:
    def test_returns_results(self, videos_soup):
        results = parse_video_results(videos_soup)
        assert len(results) > 0

    def test_result_type(self, videos_soup):
        results = parse_video_results(videos_soup)
        assert all(isinstance(r, VideoResult) for r in results)


class TestScholarParser:
    def test_returns_results(self, scholar_soup):
        results = parse_scholar_results(scholar_soup)
        assert len(results) > 0

    def test_result_type(self, scholar_soup):
        results = parse_scholar_results(scholar_soup)
        assert all(isinstance(r, ScholarResult) for r in results)

    def test_title_non_empty(self, scholar_soup):
        results = parse_scholar_results(scholar_soup)
        assert all(r.title for r in results)

    def test_url_non_empty(self, scholar_soup):
        results = parse_scholar_results(scholar_soup)
        assert all(r.url for r in results)
