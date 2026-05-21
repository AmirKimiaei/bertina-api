from __future__ import annotations

import pytest
import respx
import httpx

from bertina.radar import BertinaRadar, AsyncBertinaRadar
from bertina.radar.models import RadarPage
from bertina.exceptions import BertinaHTTPError
from tests.conftest import load_fixture

RADAR_HTML = load_fixture("radar", "radar.html")
RADAR_URL = "https://search.bertina.ir/radar"


class TestBertinaRadar:
    @respx.mock
    def test_get_returns_radar_page(self):
        respx.get(RADAR_URL).mock(return_value=httpx.Response(200, text=RADAR_HTML))
        with BertinaRadar() as radar:
            page = radar.get()
        assert isinstance(page, RadarPage)

    @respx.mock
    def test_http_error_raises(self):
        respx.get(RADAR_URL).mock(return_value=httpx.Response(503))
        with BertinaRadar(max_retries=1) as radar:
            with pytest.raises(BertinaHTTPError):
                radar.get()

    @respx.mock
    def test_debug_attaches_raw_html(self):
        respx.get(RADAR_URL).mock(return_value=httpx.Response(200, text=RADAR_HTML))
        with BertinaRadar(debug=True) as radar:
            page = radar.get()
        assert page._raw_html is not None

    @respx.mock
    def test_cache_avoids_second_request(self):
        route = respx.get(RADAR_URL).mock(
            return_value=httpx.Response(200, text=RADAR_HTML)
        )
        with BertinaRadar(cache_ttl=60) as radar:
            radar.get()
            radar.get()
        assert route.call_count == 1


class TestAsyncBertinaRadar:
    @respx.mock
    async def test_get_returns_radar_page(self):
        respx.get(RADAR_URL).mock(return_value=httpx.Response(200, text=RADAR_HTML))
        async with AsyncBertinaRadar() as radar:
            page = await radar.get()
        assert isinstance(page, RadarPage)
        assert len(page.hot) > 0
        assert len(page.important) > 0
