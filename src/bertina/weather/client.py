from __future__ import annotations

import logging
from typing import Any

from .._base import AsyncBaseClient, BaseClient
from ..exceptions import BertinaParseError
from .models import WeatherCurrent, WeatherDay, WeatherForecast, WeatherHour

logger = logging.getLogger("bertina.weather")

_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_CURRENT_PARAMS = ",".join(
    [
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "wind_speed_10m",
        "wind_direction_10m",
        "weather_code",
        "surface_pressure",
        "visibility",
        "uv_index",
        "precipitation",
    ]
)

_WMO_LABELS = {
    0: "آسمان صاف",
    1: "عمدتاً صاف",
    2: "نیمه ابری",
    3: "ابری",
    45: "مه آلود",
    48: "مه یخبندان",
    51: "نم نم باران",
    53: "باران خفیف",
    55: "باران متوسط",
    61: "باران سبک",
    63: "باران متوسط",
    65: "باران سنگین",
    71: "برف سبک",
    73: "برف متوسط",
    75: "برف سنگین",
    80: "رگبار سبک",
    81: "رگبار متوسط",
    82: "رگبار سنگین",
    95: "طوفان رعد و برق",
    96: "طوفان با تگرگ",
    99: "طوفان با تگرگ سنگین",
}


def _wmo_label(code: int) -> str:
    return _WMO_LABELS.get(code, str(code))


def _geocode(client_get: Any, city: str) -> tuple[str, float, float]:
    """Return (name, lat, lon) for the first geocoding result."""
    data = client_get(_GEOCODING_URL, {"name": city, "count": 1, "language": "fa"})
    import json

    results = json.loads(data).get("results") or []
    if not results:
        raise BertinaParseError(f"city not found: {city!r}")
    r = results[0]
    return r.get("name", city), float(r["latitude"]), float(r["longitude"])


async def _ageocide(client_aget: Any, city: str) -> tuple[str, float, float]:
    data = await client_aget(
        _GEOCODING_URL, {"name": city, "count": 1, "language": "fa"}
    )
    import json

    results = json.loads(data).get("results") or []
    if not results:
        raise BertinaParseError(f"city not found: {city!r}")
    r = results[0]
    return r.get("name", city), float(r["latitude"]), float(r["longitude"])


def _build_forecast_params(lat: float, lon: float) -> dict:
    return {
        "latitude": lat,
        "longitude": lon,
        "current": _CURRENT_PARAMS,
        "hourly": "temperature_2m,weather_code,precipitation_probability",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max,sunrise,sunset",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
        "forecast_days": 7,
    }


def _parse_forecast(
    data: dict, location: str, lat: float, lon: float
) -> WeatherForecast:
    import json as _json

    if isinstance(data, str):
        data = _json.loads(data)

    cur = data.get("current", {})
    current = WeatherCurrent(
        location=location,
        latitude=lat,
        longitude=lon,
        temperature=cur.get("temperature_2m", 0.0),
        feels_like=cur.get("apparent_temperature", 0.0),
        humidity=int(cur.get("relative_humidity_2m", 0)),
        wind_speed=cur.get("wind_speed_10m", 0.0),
        wind_direction=int(cur.get("wind_direction_10m", 0)),
        condition=_wmo_label(int(cur.get("weather_code", 0))),
        pressure=cur.get("surface_pressure", 0.0),
        visibility=cur.get("visibility", 0.0),
        uv_index=cur.get("uv_index", 0.0),
        precipitation=cur.get("precipitation", 0.0),
    )

    hourly_data = data.get("hourly", {})
    times = hourly_data.get("time", [])
    temps = hourly_data.get("temperature_2m", [])
    codes = hourly_data.get("weather_code", [])
    precips = hourly_data.get("precipitation_probability", [])
    hourly = [
        WeatherHour(
            time=times[i],
            temperature=temps[i],
            condition=_wmo_label(int(codes[i])),
            precipitation_probability=int(precips[i] or 0),
        )
        for i in range(len(times))
    ]

    daily_data = data.get("daily", {})
    dates = daily_data.get("time", [])
    maxes = daily_data.get("temperature_2m_max", [])
    mins = daily_data.get("temperature_2m_min", [])
    dcodes = daily_data.get("weather_code", [])
    dprecips = daily_data.get("precipitation_probability_max", [])
    sunrises = daily_data.get("sunrise", [])
    sunsets = daily_data.get("sunset", [])
    daily = [
        WeatherDay(
            date=dates[i],
            condition=_wmo_label(int(dcodes[i])),
            temp_max=maxes[i],
            temp_min=mins[i],
            precipitation_probability=int(dprecips[i] or 0),
            sunrise=sunrises[i],
            sunset=sunsets[i],
        )
        for i in range(len(dates))
    ]

    return WeatherForecast(
        location=location,
        latitude=lat,
        longitude=lon,
        current=current,
        hourly=hourly,
        daily=daily,
    )


class BertinaWeather(BaseClient):
    """Synchronous Bertina weather client (data from open-meteo.com)."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or 1800, **kwargs)

    def forecast(self, city: str) -> WeatherForecast:
        location, lat, lon = _geocode(self._get, city)
        logger.debug("weather forecast city=%r lat=%s lon=%s", city, lat, lon)
        raw = self._get(_FORECAST_URL, _build_forecast_params(lat, lon))
        import json

        return _parse_forecast(json.loads(raw), location, lat, lon)


class AsyncBertinaWeather(AsyncBaseClient):
    """Asynchronous Bertina weather client (data from open-meteo.com)."""

    def __init__(self, *, cache_ttl: int | None = None, **kwargs: Any) -> None:
        super().__init__(cache_ttl=cache_ttl or 1800, **kwargs)

    async def forecast(self, city: str) -> WeatherForecast:
        location, lat, lon = await _ageocide(self._aget, city)
        logger.debug("weather forecast city=%r lat=%s lon=%s", city, lat, lon)
        raw = await self._aget(_FORECAST_URL, _build_forecast_params(lat, lon))
        import json

        return _parse_forecast(json.loads(raw), location, lat, lon)
