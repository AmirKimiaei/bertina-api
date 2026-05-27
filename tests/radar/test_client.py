from __future__ import annotations

from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from bertina.radar import BertinaRadar, AsyncBertinaRadar
from bertina.radar.models import RadarPage
from bertina.exceptions import BertinaHTTPError
from tests.conftest import load_fixture

RADAR_HTML = load_fixture("radar", "radar.html")
RADAR_URL = "https://search.bertina.ir/radar"


class TestBertinaRadar:
    def test_get_returns_radar_page(self):
        with patch.object(BertinaRadar, "_get", return_value=RADAR_HTML):
            with BertinaRadar() as radar:
                page = radar.get()
        assert isinstance(page, RadarPage)

    def test_http_error_raises(self):
        with patch.object(BertinaRadar, "_get", side_effect=BertinaHTTPError("HTTP 503", 503)):
            with BertinaRadar() as radar:
                with pytest.raises(BertinaHTTPError):
                    radar.get()

    def test_debug_attaches_raw_html(self):
        with patch.object(BertinaRadar, "_get", return_value=RADAR_HTML):
            with BertinaRadar(debug=True) as radar:
                page = radar.get()
        assert page._raw_html is not None

    def test_cache_avoids_second_request(self):
        mock_resp = MagicMock(status_code=200, text=RADAR_HTML)
        radar = BertinaRadar(cache_ttl=60)
        with patch.object(radar._client, "get", return_value=mock_resp) as mock_get:
            radar.get()
            radar.get()
        assert mock_get.call_count == 1
        radar.close()


class TestAsyncBertinaRadar:
    async def test_get_returns_radar_page(self):
        with patch.object(AsyncBertinaRadar, "_aget", new_callable=AsyncMock, return_value=RADAR_HTML):
            async with AsyncBertinaRadar() as radar:
                page = await radar.get()
        assert isinstance(page, RadarPage)
        assert len(page.hot) > 0
        assert len(page.important) > 0
