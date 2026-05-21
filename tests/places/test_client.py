from __future__ import annotations

import pytest
import respx
import httpx

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
    @respx.mock
    def test_get_provinces(self):
        respx.get(f"{BASE}/places").mock(
            return_value=httpx.Response(200, text=PROVINCES_HTML)
        )
        with BertinaPlaces() as client:
            provinces = client.get_provinces()
        assert len(provinces) == 32
        assert all(isinstance(p, Province) for p in provinces)

    @respx.mock
    def test_get_city(self):
        respx.get(url__regex=rf"{BASE}/places/.*").mock(
            return_value=httpx.Response(200, text=CITY_HTML)
        )
        with BertinaPlaces() as client:
            cats = client.get_city("تهران")
        assert len(cats) > 0
        assert all(isinstance(c, PlacesCategory) for c in cats)

    @respx.mock
    def test_get_category(self):
        respx.get(url__regex=rf"{BASE}/places/.*").mock(
            return_value=httpx.Response(200, text=CATEGORY_HTML)
        )
        with BertinaPlaces() as client:
            cards = client.get_category("تهران", "کافه")
        assert len(cards) > 0
        assert all(isinstance(c, PlaceCard) for c in cards)

    @respx.mock
    def test_get_place(self):
        respx.get(f"{BASE}/place/hilo-cafe").mock(
            return_value=httpx.Response(200, text=DETAIL_HTML)
        )
        with BertinaPlaces() as client:
            detail = client.get_place("hilo-cafe")
        assert isinstance(detail, PlaceDetail)
        assert detail.name == "Hilo cafe"
        assert detail.slug == "hilo-cafe"

    @respx.mock
    def test_http_error_raises(self):
        respx.get(f"{BASE}/places").mock(return_value=httpx.Response(503))
        with BertinaPlaces(max_retries=1) as client:
            with pytest.raises(BertinaHTTPError):
                client.get_provinces()


class TestAsyncBertinaPlaces:
    @respx.mock
    async def test_get_provinces(self):
        respx.get(f"{BASE}/places").mock(
            return_value=httpx.Response(200, text=PROVINCES_HTML)
        )
        async with AsyncBertinaPlaces() as client:
            provinces = await client.get_provinces()
        assert len(provinces) == 32

    @respx.mock
    async def test_get_place(self):
        respx.get(f"{BASE}/place/hilo-cafe").mock(
            return_value=httpx.Response(200, text=DETAIL_HTML)
        )
        async with AsyncBertinaPlaces() as client:
            detail = await client.get_place("hilo-cafe")
        assert detail.name == "Hilo cafe"
        assert detail.city == "تهران"
