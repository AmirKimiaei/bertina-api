from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class WeatherCurrent:
    location: str
    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    wind_direction: int
    condition: str
    pressure: float
    visibility: float
    uv_index: float
    precipitation: float


@dataclass(slots=True)
class WeatherHour:
    time: str
    temperature: float
    condition: str
    precipitation_probability: int


@dataclass(slots=True)
class WeatherDay:
    date: str
    condition: str
    temp_max: float
    temp_min: float
    precipitation_probability: int
    sunrise: str
    sunset: str


@dataclass(slots=True)
class WeatherForecast:
    location: str
    latitude: float
    longitude: float
    current: WeatherCurrent
    hourly: list[WeatherHour] = field(default_factory=list)
    daily: list[WeatherDay] = field(default_factory=list)
