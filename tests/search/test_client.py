from __future__ import annotations

import pytest
import respx
import httpx

from bertina.search import BertinaSearch, AsyncBertinaSearch, SearchType
from bertina.search.models import SearchResponse, WebResult, NewsResult, ScholarResult
from bertina.exceptions import BertinaHTTPError, BertinaRateLimitError
from tests.conftest import load_fixture

WEB_HTML = load_fixture("search", "web.html")
NEWS_HTML = load_fixture("search", "news.html")
SCHOLAR_HTML = load_fixture("search", "scholar.html")
SEARCH_URL = "https://search.bertina.ir/search"


class TestBertinaSearch:
    @respx.mock
    def test_web_search_returns_response(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=WEB_HTML))
        with BertinaSearch() as client:
            resp = client.search("python")
        assert isinstance(resp, SearchResponse)
        assert resp.query == "python"
        assert resp.page == 1
        assert resp.search_type == SearchType.WEB
        assert len(resp.results) > 0

    @respx.mock
    def test_news_search_returns_news_results(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=NEWS_HTML))
        with BertinaSearch() as client:
            resp = client.search("python", type=SearchType.NEWS)
        assert resp.search_type == SearchType.NEWS
        assert all(isinstance(r, NewsResult) for r in resp.results)

    @respx.mock
    def test_pagination_param(self):
        route = respx.get(SEARCH_URL).mock(
            return_value=httpx.Response(200, text=WEB_HTML)
        )
        with BertinaSearch() as client:
            client.search("python", page=2)
        assert route.called
        request = route.calls[0].request
        assert b"page=2" in request.url.query

    @respx.mock
    def test_web_type_has_no_type_param(self):
        route = respx.get(SEARCH_URL).mock(
            return_value=httpx.Response(200, text=WEB_HTML)
        )
        with BertinaSearch() as client:
            client.search("python", type=SearchType.WEB)
        request = route.calls[0].request
        assert b"type=" not in request.url.query

    @respx.mock
    def test_news_type_adds_type_param(self):
        route = respx.get(SEARCH_URL).mock(
            return_value=httpx.Response(200, text=NEWS_HTML)
        )
        with BertinaSearch() as client:
            client.search("python", type=SearchType.NEWS)
        request = route.calls[0].request
        assert b"type=news" in request.url.query

    @respx.mock
    def test_http_error_raises(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(500))
        with BertinaSearch(max_retries=1) as client:
            with pytest.raises(BertinaHTTPError) as exc_info:
                client.search("python")
        assert exc_info.value.status_code == 500

    @respx.mock
    def test_rate_limit_raises(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(429))
        with BertinaSearch(max_retries=1) as client:
            with pytest.raises(BertinaRateLimitError):
                client.search("python")

    @respx.mock
    def test_debug_attaches_raw_html(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=WEB_HTML))
        with BertinaSearch(debug=True) as client:
            resp = client.search("python")
        assert resp._raw_html is not None
        assert len(resp._raw_html) > 0

    @respx.mock
    def test_no_raw_html_without_debug(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=WEB_HTML))
        with BertinaSearch(debug=False) as client:
            resp = client.search("python")
        assert resp._raw_html is None

    @respx.mock
    def test_cache_avoids_second_request(self):
        route = respx.get(SEARCH_URL).mock(
            return_value=httpx.Response(200, text=WEB_HTML)
        )
        with BertinaSearch(cache_ttl=60) as client:
            client.search("python")
            client.search("python")
        assert route.call_count == 1

    @respx.mock
    def test_context_manager(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=WEB_HTML))
        with BertinaSearch() as client:
            resp = client.search("python")
        assert isinstance(resp, SearchResponse)


class TestAsyncBertinaSearch:
    @respx.mock
    async def test_web_search_returns_response(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=WEB_HTML))
        async with AsyncBertinaSearch() as client:
            resp = await client.search("python")
        assert isinstance(resp, SearchResponse)
        assert len(resp.results) > 0

    @respx.mock
    async def test_scholar_search(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=SCHOLAR_HTML))
        async with AsyncBertinaSearch() as client:
            resp = await client.search("python", type=SearchType.SCHOLAR)
        assert resp.search_type == SearchType.SCHOLAR
        assert all(isinstance(r, ScholarResult) for r in resp.results)

    @respx.mock
    async def test_check_alive_sets_is_alive(self):
        respx.get(SEARCH_URL).mock(return_value=httpx.Response(200, text=WEB_HTML))
        respx.head(url__regex=r"https?://.*").mock(return_value=httpx.Response(200))
        async with AsyncBertinaSearch() as client:
            resp = await client.search("python")
            resp = await client.check_alive(resp)
        web_results = [r for r in resp.results if isinstance(r, WebResult)]
        assert all(r.is_alive is not None for r in web_results)
