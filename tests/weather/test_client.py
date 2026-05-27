from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from bertina.exceptions import BertinaHTTPError, BertinaParseError
from bertina.weather import AsyncBertinaWeather, BertinaWeather, WeatherForecast


def _geocoding_response(
    name: str = "Tehran", lat: float = 35.69, lon: float = 51.42
) -> dict:
    return {
        "results": [
            {"name": name, "latitude": lat, "longitude": lon, "country": "Iran"}
        ]
    }


def _forecast_response() -> dict:
    return {
        "current": {
            "temperature_2m": 22.0,
            "apparent_temperature": 20.5,
            "relative_humidity_2m": 45,
            "wind_speed_10m": 10.0,
            "wind_direction_10m": 180,
            "weather_code": 1,
            "surface_pressure": 1013.0,
            "visibility": 10000.0,
            "uv_index": 3.0,
            "precipitation": 0.0,
        },
        "hourly": {
            "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
            "temperature_2m": [20.0, 19.0],
            "weather_code": [0, 1],
            "precipitation_probability": [5, 10],
        },
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "temperature_2m_max": [24.0, 26.0],
            "temperature_2m_min": [14.0, 15.0],
            "weather_code": [1, 2],
            "precipitation_probability_max": [10, 20],
            "sunrise": ["2024-01-01T07:00", "2024-01-02T07:01"],
            "sunset": ["2024-01-01T17:30", "2024-01-02T17:31"],
        },
    }


class TestBertinaWeather:
    def test_forecast_returns_weather_forecast(self):
        responses = [json.dumps(_geocoding_response()), json.dumps(_forecast_response())]
        with patch.object(BertinaWeather, "_get", side_effect=responses):
            with BertinaWeather() as client:
                result = client.forecast("Tehran")
        assert isinstance(result, WeatherForecast)

    def test_forecast_location_name(self):
        responses = [json.dumps(_geocoding_response("تهران")), json.dumps(_forecast_response())]
        with patch.object(BertinaWeather, "_get", side_effect=responses):
            with BertinaWeather() as client:
                result = client.forecast("تهران")
        assert result.location == "تهران"

    def test_current_weather_fields(self):
        responses = [json.dumps(_geocoding_response()), json.dumps(_forecast_response())]
        with patch.object(BertinaWeather, "_get", side_effect=responses):
            with BertinaWeather() as client:
                result = client.forecast("Tehran")
        assert result.current.temperature == 22.0
        assert result.current.feels_like == 20.5
        assert result.current.humidity == 45
        assert result.current.wind_speed == 10.0
        assert result.current.condition == "عمدتاً صاف"

    def test_daily_forecast_count(self):
        responses = [json.dumps(_geocoding_response()), json.dumps(_forecast_response())]
        with patch.object(BertinaWeather, "_get", side_effect=responses):
            with BertinaWeather() as client:
                result = client.forecast("Tehran")
        assert len(result.daily) == 2
        assert result.daily[0].temp_max == 24.0
        assert result.daily[0].temp_min == 14.0

    def test_hourly_forecast_count(self):
        responses = [json.dumps(_geocoding_response()), json.dumps(_forecast_response())]
        with patch.object(BertinaWeather, "_get", side_effect=responses):
            with BertinaWeather() as client:
                result = client.forecast("Tehran")
        assert len(result.hourly) == 2
        assert result.hourly[0].temperature == 20.0

    def test_city_not_found_raises_parse_error(self):
        with patch.object(BertinaWeather, "_get", return_value=json.dumps({"results": []})):
            with BertinaWeather() as client:
                with pytest.raises(BertinaParseError, match="city not found"):
                    client.forecast("xyznotacity")

    def test_geocoding_http_error_raises(self):
        with patch.object(BertinaWeather, "_get", side_effect=BertinaHTTPError("HTTP 500", 500)):
            with BertinaWeather() as client:
                with pytest.raises(BertinaHTTPError):
                    client.forecast("Tehran")

    def test_coordinates_from_geocoding(self):
        responses = [
            json.dumps(_geocoding_response(lat=35.69, lon=51.42)),
            json.dumps(_forecast_response()),
        ]
        with patch.object(BertinaWeather, "_get", side_effect=responses):
            with BertinaWeather() as client:
                result = client.forecast("Tehran")
        assert result.latitude == pytest.approx(35.69)
        assert result.longitude == pytest.approx(51.42)


class TestAsyncBertinaWeather:
    async def test_forecast_returns_weather_forecast(self):
        responses = [json.dumps(_geocoding_response("تهران")), json.dumps(_forecast_response())]
        with patch.object(AsyncBertinaWeather, "_aget", new_callable=AsyncMock, side_effect=responses):
            async with AsyncBertinaWeather() as client:
                result = await client.forecast("تهران")
        assert isinstance(result, WeatherForecast)
        assert result.location == "تهران"
        assert len(result.daily) == 2

    async def test_city_not_found_raises(self):
        with patch.object(AsyncBertinaWeather, "_aget", new_callable=AsyncMock, return_value=json.dumps({"results": []})):
            async with AsyncBertinaWeather() as client:
                with pytest.raises(BertinaParseError):
                    await client.forecast("xyznotacity")
