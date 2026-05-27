from __future__ import annotations

from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from bertina.search import BertinaSearch, AsyncBertinaSearch, SearchType
from bertina.search.models import SearchResponse, WebResult, NewsResult, ScholarResult
from bertina.exceptions import BertinaHTTPError, BertinaRateLimitError
from tests.conftest import load_fixture

WEB_HTML = load_fixture("search", "web.html")
NEWS_HTML = load_fixture("search", "news.html")
SCHOLAR_HTML = load_fixture("search", "scholar.html")
SEARCH_URL = "https://search.bertina.ir/search"


class TestBertinaSearch:
    def test_web_search_returns_response(self):
        with patch.object(BertinaSearch, "_get", return_value=WEB_HTML):
            with BertinaSearch() as client:
                resp = client.search("python")
        assert isinstance(resp, SearchResponse)
        assert resp.query == "python"
        assert resp.page == 1
        assert resp.search_type == SearchType.WEB
        assert len(resp.results) > 0

    def test_news_search_returns_news_results(self):
        with patch.object(BertinaSearch, "_get", return_value=NEWS_HTML):
            with BertinaSearch() as client:
                resp = client.search("python", type=SearchType.NEWS)
        assert resp.search_type == SearchType.NEWS
        assert all(isinstance(r, NewsResult) for r in resp.results)

    def test_pagination_param(self):
        with patch.object(BertinaSearch, "_get", return_value=WEB_HTML) as mock_get:
            with BertinaSearch() as client:
                client.search("python", page=2)
        url, params = mock_get.call_args.args
        assert params.get("page") == 2

    def test_web_type_has_no_type_param(self):
        with patch.object(BertinaSearch, "_get", return_value=WEB_HTML) as mock_get:
            with BertinaSearch() as client:
                client.search("python", type=SearchType.WEB)
        url, params = mock_get.call_args.args
        assert "type" not in params

    def test_news_type_adds_type_param(self):
        with patch.object(BertinaSearch, "_get", return_value=NEWS_HTML) as mock_get:
            with BertinaSearch() as client:
                client.search("python", type=SearchType.NEWS)
        url, params = mock_get.call_args.args
        assert params.get("type") == "news"

    def test_http_error_raises(self):
        with patch.object(BertinaSearch, "_get", side_effect=BertinaHTTPError("HTTP 500", 500)):
            with BertinaSearch() as client:
                with pytest.raises(BertinaHTTPError) as exc_info:
                    client.search("python")
        assert exc_info.value.status_code == 500

    def test_rate_limit_raises(self):
        with patch.object(BertinaSearch, "_get", side_effect=BertinaRateLimitError()):
            with BertinaSearch() as client:
                with pytest.raises(BertinaRateLimitError):
                    client.search("python")

    def test_debug_attaches_raw_html(self):
        with patch.object(BertinaSearch, "_get", return_value=WEB_HTML):
            with BertinaSearch(debug=True) as client:
                resp = client.search("python")
        assert resp._raw_html is not None
        assert len(resp._raw_html) > 0

    def test_no_raw_html_without_debug(self):
        with patch.object(BertinaSearch, "_get", return_value=WEB_HTML):
            with BertinaSearch(debug=False) as client:
                resp = client.search("python")
        assert resp._raw_html is None

    def test_cache_avoids_second_request(self):
        mock_resp = MagicMock(status_code=200, text=WEB_HTML)
        client = BertinaSearch(cache_ttl=60)
        with patch.object(client._client, "get", return_value=mock_resp) as mock_get:
            client.search("python")
            client.search("python")
        assert mock_get.call_count == 1
        client.close()

    def test_context_manager(self):
        with patch.object(BertinaSearch, "_get", return_value=WEB_HTML):
            with BertinaSearch() as client:
                resp = client.search("python")
        assert isinstance(resp, SearchResponse)


class TestAsyncBertinaSearch:
    async def test_web_search_returns_response(self):
        with patch.object(AsyncBertinaSearch, "_aget", new_callable=AsyncMock, return_value=WEB_HTML):
            async with AsyncBertinaSearch() as client:
                resp = await client.search("python")
        assert isinstance(resp, SearchResponse)
        assert len(resp.results) > 0

    async def test_scholar_search(self):
        with patch.object(AsyncBertinaSearch, "_aget", new_callable=AsyncMock, return_value=SCHOLAR_HTML):
            async with AsyncBertinaSearch() as client:
                resp = await client.search("python", type=SearchType.SCHOLAR)
        assert resp.search_type == SearchType.SCHOLAR
        assert all(isinstance(r, ScholarResult) for r in resp.results)

    async def test_check_alive_sets_is_alive(self):
        with patch.object(AsyncBertinaSearch, "_aget", new_callable=AsyncMock, return_value=WEB_HTML):
            async with AsyncBertinaSearch() as client:
                resp = await client.search("python")
                with patch.object(AsyncBertinaSearch, "check_url_alive", new_callable=AsyncMock, return_value=True):
                    resp = await client.check_alive(resp)
        web_results = [r for r in resp.results if isinstance(r, WebResult)]
        assert all(r.is_alive is not None for r in web_results)
