from __future__ import annotations

from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from bertina.places import BertinaPlaces, AsyncBertinaPlaces
from bertina.places.models import PlaceCard, PlaceDetail, PlacesCategory, Province
from bertina.exceptions import BertinaHTTPError
from tests.conftest import load_fixture

PROVINCES_HTML = load_fixture("places", "provinces.html")
CITY_HTML = load_fixture("places", "city.html")
CATEGORY_HTML = load_fixture("places", "category.html")
DETAIL_HTML = load_fixture("places", "detail.html")
BASE = "https://search.bertina.ir"


class TestBertinaPlaces:
    def test_get_provinces(self):
        with patch.object(BertinaPlaces, "_get", return_value=PROVINCES_HTML):
            with BertinaPlaces() as client:
                provinces = client.get_provinces()
        assert len(provinces) == 32
        assert all(isinstance(p, Province) for p in provinces)

    def test_get_city(self):
        with patch.object(BertinaPlaces, "_get", return_value=CITY_HTML):
            with BertinaPlaces() as client:
                cats = client.get_city("تهران")
        assert len(cats) > 0
        assert all(isinstance(c, PlacesCategory) for c in cats)

    def test_get_category(self):
        with patch.object(BertinaPlaces, "_get", return_value=CATEGORY_HTML):
            with BertinaPlaces() as client:
                cards = client.get_category("تهران", "کافه")
        assert len(cards) > 0
        assert all(isinstance(c, PlaceCard) for c in cards)

    def test_get_place(self):
        with patch.object(BertinaPlaces, "_get", return_value=DETAIL_HTML):
            with BertinaPlaces() as client:
                detail = client.get_place("hilo-cafe")
        assert isinstance(detail, PlaceDetail)
        assert detail.name == "Hilo cafe"
        assert detail.slug == "hilo-cafe"

    def test_http_error_raises(self):
        with patch.object(BertinaPlaces, "_get", side_effect=BertinaHTTPError("HTTP 503", 503)):
            with BertinaPlaces() as client:
                with pytest.raises(BertinaHTTPError):
                    client.get_provinces()


class TestAsyncBertinaPlaces:
    async def test_get_provinces(self):
        with patch.object(AsyncBertinaPlaces, "_aget", new_callable=AsyncMock, return_value=PROVINCES_HTML):
            async with AsyncBertinaPlaces() as client:
                provinces = await client.get_provinces()
        assert len(provinces) == 32

    async def test_get_place(self):
        with patch.object(AsyncBertinaPlaces, "_aget", new_callable=AsyncMock, return_value=DETAIL_HTML):
            async with AsyncBertinaPlaces() as client:
                detail = await client.get_place("hilo-cafe")
        assert detail.name == "Hilo cafe"
        assert detail.city == "تهران"
