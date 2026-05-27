# bertina-api

A Python SDK for the [Bertina](https://search.bertina.ir) ecosystem — search, news radar, places, translation, and weather.

Bertina is a Persian AI-powered search engine. This library wraps its public pages into clean, typed Python objects with full async support, automatic retries, caching, and more.

---

## Features

- **7 search types** — web, news, shopping, places, images, videos, scholarly articles
- **News radar** — trending hot and important topics with entities, sources, and timestamps
- **Website alive check** — detect which search result URLs are reachable
- Sync and **async** clients for every service
- Typed `dataclass` models — no raw dicts
- Automatic **retry** with exponential backoff on network failures
- In-memory **TTL cache** — reduces repeated requests
- **Async rate limiter** — configurable concurrency limit
- **Debug mode** — attach raw HTML to any response
- **Proxy support**
- **Bot detection avoidance** — Chrome TLS fingerprint, real browser headers, and randomised request pacing

---

## Installation

### Option 1 — Install from remote (recommended)

```bash
pip install git+https://git.zwire.ir/mattco/beartina-api.git
```

### Option 2 — Clone and install locally

```bash
git clone https://git.zwire.ir/mattco/beartina-api.git
cd bertina-api

python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows

pip install -e .
```

---

## Quick Start

```python
from bertina.search import BertinaSearch, SearchType

with BertinaSearch() as client:
    resp = client.search("هوش مصنوعی", type=SearchType.WEB)
    for r in resp.results:
        print(r.title)
        print(r.url)
```

---

## Modules

### `bertina.search` — Search

Supports 7 search types via the `SearchType` enum:

| Value | Description |
|---|---|
| `SearchType.WEB` | Web results (default) |
| `SearchType.NEWS` | News articles |
| `SearchType.SHOPPING` | Shopping / product listings |
| `SearchType.PLACES` | Local businesses and locations |
| `SearchType.IMAGES` | Image results |
| `SearchType.VIDEOS` | Video results |
| `SearchType.SCHOLAR` | Scholarly / academic articles |

**Sync usage:**
```python
from bertina.search import BertinaSearch, SearchType

with BertinaSearch() as client:
    # Web search
    resp = client.search("python", type=SearchType.WEB)
    print(resp.results[0].title)
    print(resp.results[0].url)

    # News search
    resp = client.search("ایران", type=SearchType.NEWS)
    for r in resp.results:
        print(r.title, "|", r.source, "|", r.published_at)

    # Shopping
    resp = client.search("لپ تاپ", type=SearchType.SHOPPING)
    for r in resp.results:
        print(r.title, "|", r.merchant)

    # Scholar
    resp = client.search("machine learning", type=SearchType.SCHOLAR)
    for r in resp.results:
        print(r.title, "|", r.authors_and_year, "|", r.citations, "citations")

    # Pagination
    resp = client.search("python", page=2)
```

**Async usage:**
```python
import asyncio
from bertina.search import AsyncBertinaSearch, SearchType

async def main():
    async with AsyncBertinaSearch() as client:
        resp = await client.search("python", type=SearchType.SCHOLAR)
        for r in resp.results:
            print(r.title)

asyncio.run(main())
```

---

#### Website Alive Check

After a web search, you can check which result URLs are reachable:

```python
from bertina.search import BertinaSearch, SearchType

with BertinaSearch() as client:
    resp = client.search("python", type=SearchType.WEB)
    resp = client.check_alive(resp)            # checks each URL

    for r in resp.results:
        icon = "🟢" if r.is_alive else "🔴"
        print(f"{icon} {r.title}")
        print(f"   {r.url}")
```

`is_alive` values:
- `True` — website responded successfully
- `False` — website is unreachable or returned an error
- `None` — not checked yet (default)

**Async alive check** — checks all URLs concurrently (much faster):
```python
async with AsyncBertinaSearch() as client:
    resp = await client.search("python")
    resp = await client.check_alive(resp)      # concurrent checks
    for r in resp.results:
        print("🟢" if r.is_alive else "🔴", r.title)
```

---

#### Result Models

**`WebResult`**
```
title        — page title
url          — destination URL (decoded from Bertina's click tracker)
description  — text snippet
favicon_url  — site icon URL
sitelinks    — list of sub-links shown under the result
is_alive     — bool | None (populated by check_alive())
```

**`NewsResult`**
```
title        — article headline
url          — article URL
source       — publisher name (e.g. "Yahoo", "فارس نیوز")
published_at — relative time (e.g. "۳ ساعت پیش")
thumbnail    — image URL
```

**`ShoppingResult`**
```
title           — product name
url             — product page URL
description     — product description
merchant        — store name (e.g. "ترب")
merchant_domain — store domain (e.g. "torob.com")
buy_url         — direct purchase link
```

**`ScholarResult`**
```
title            — paper title
url              — paper URL
authors_and_year — e.g. "G Van Rossum, FL Drake - 2003"
citations        — citation count
year             — publication year
description      — abstract excerpt
is_pdf           — True if a PDF link is available
```

**`ImageResult`** / **`VideoResult`**
```
title      — title / alt text
thumbnail  — thumbnail image URL
source     — source domain
```

**`SearchResponse`**
```
query        — original search query
page         — current page number
search_type  — SearchType enum value
results      — list of result objects
related      — list of related search suggestions
_raw_html    — raw HTML (only when debug=True)
```

---

### `bertina.radar` — News Radar

Fetches trending news topics from [search.bertina.ir/radar](https://search.bertina.ir/radar).

```python
from bertina.radar import BertinaRadar

with BertinaRadar() as radar:
    page = radar.get()

    print("Last updated:", page.last_updated)
    print(f"Hot topics ({len(page.hot)}):")
    for item in page.hot[:5]:
        print(f"  {item.rank}. {item.title}")
        print(f"     Category: {item.category}")
        print(f"     Source:   {item.source} | {item.published_at}")
        print(f"     Entities: {item.entities}")
```

**Async:**
```python
async with AsyncBertinaRadar() as radar:
    page = await radar.get()
    print(page.hot[0].title)
```

**`RadarItem`**
```
rank         — position (1, 2, 3 ...)
title        — topic headline
category     — e.g. "سیاست جهانی", "اقتصاد"
subtopic     — sub-category tag
summary      — short article summary
source       — news source name
published_at — relative time (e.g. "۱ ساعت پیش")
thumbnail    — image URL
entities     — list of related named entities (people, places, orgs)
news_url     — link to search news about this topic
```

**`RadarPage`**
```
hot          — list[RadarItem] — trending in last 2 hours (25 items)
important    — list[RadarItem] — sustained trends last 24 hours (21 items)
last_updated — last refresh timestamp
```

---

### `bertina.places` — Places Directory

Browse Iran's business directory across 32 provinces and 1,014 cities.

**Browse provinces and cities:**
```python
from bertina.places import BertinaPlaces

with BertinaPlaces() as client:
    provinces = client.get_provinces()
    print(f"{len(provinces)} provinces")
    for province in provinces[:2]:
        print(f"\n{province.name} ({len(province.cities)} cities)")
        for city in province.cities[:3]:
            print(f"  {city.name} — {city.place_count}")
            print(f"  Top categories: {city.categories}")
```

**Browse categories in a city:**
```python
with BertinaPlaces() as client:
    categories = client.get_city("تهران")
    for cat in categories[:5]:
        print(f"{cat.name} — {cat.place_count}")
```

**List places in a city/category:**
```python
with BertinaPlaces() as client:
    cards = client.get_category("تهران", "کافه")
    for place in cards:
        print(f"{place.name} | {place.neighbourhood} | rating: {place.rating}")
        print(f"  {place.url}")
```

**Get full place detail:**
```python
with BertinaPlaces() as client:
    detail = client.get_place("hilo-cafe")
    print(detail.name, "|", detail.city, "|", detail.neighbourhood)
    print("Rating:", detail.rating, f"({detail.rating_count} reviews)")
    print("Address:", detail.address)
    print("Coordinates:", detail.latitude, detail.longitude)
    print("Category:", detail.category)
    print("Phone:", detail.phone)
    print("Website:", detail.website)
    for day, hours in detail.opening_hours.items():
        print(f"  {day}: {hours}")
```

**Async:**
```python
import asyncio
from bertina.places import AsyncBertinaPlaces

async def main():
    async with AsyncBertinaPlaces() as client:
        provinces = await client.get_provinces()
        categories = await client.get_city("اصفهان")
        cards = await client.get_category("اصفهان", "رستوران")
        detail = await client.get_place(cards[0].slug)
        print(detail.name)

asyncio.run(main())
```

**`Province`**
```
name     — province name (e.g. "استان تهران")
cities   — list[City]
```

**`City`**
```
name         — city name (e.g. "تهران")
url          — full URL to city's places page
place_count  — formatted count (e.g. "۲۶,۱۷۷ مکان")
categories   — list of top category names in that city
```

**`PlacesCategory`**
```
name         — category name (e.g. "کافه")
url          — full URL to category listing
place_count  — formatted count (e.g. "۴,۰۹۸ مکان")
```

**`PlaceCard`**
```
name          — place name
url           — place detail URL
slug          — URL slug (e.g. "hilo-cafe")
neighbourhood — neighbourhood name
rating        — rating string (if available)
thumbnail     — thumbnail image URL
```

**`PlaceDetail`**
```
name           — place name
slug           — URL slug
city           — city name
neighbourhood  — neighbourhood name
description    — description text
address        — street address
latitude       — GPS latitude (float)
longitude      — GPS longitude (float)
rating         — rating score (float)
rating_count   — number of reviews (int)
category       — place type (e.g. "کافه")
phone          — phone number
website        — website URL
opening_hours  — dict mapping day name → hours string
thumbnail      — thumbnail image URL
```

---

### `bertina.translate` — Translation

Translate text between 34 languages using the Bertina translation API.

```python
from bertina.translate import BertinaTranslate, Language

with BertinaTranslate() as client:
    result = client.translate("Hello world", target=Language.FA)
    print(result.translated_text)   # سلام دنیا
    print(result.source_lang)       # Language.AUTO
    print(result.target_lang)       # Language.FA
    print(result.detected_lang)     # Language.EN (auto-detected)
```

**Specify source language:**
```python
with BertinaTranslate() as client:
    result = client.translate("سلام دنیا", source=Language.FA, target=Language.EN)
    print(result.translated_text)   # Hello world
```

**Async:**
```python
from bertina.translate import AsyncBertinaTranslate, Language

async with AsyncBertinaTranslate() as client:
    result = await client.translate("Bonjour", target=Language.EN)
```

**`TranslationResult`**
```
source_text      — original input text
translated_text  — translated output
source_lang      — source language (Language.AUTO if auto-detect was used)
target_lang      — target language
detected_lang    — detected language (Language or None if source was specified)
```

**Supported languages (`Language` enum — 34 values):**
`AUTO, FA, EN, AR, DE, FR, ES, IT, PT, RU, ZH, JA, KO, HI, BN, TR, VI, UR, ID, PL, RO, NL, TH, CS, EL, PS, SV, BG, KK, AZ, KU, HU, MY, UK`

---

### `bertina.weather` — Weather Forecasts

Get current weather and 7-day forecasts for any city (powered by open-meteo.com, the same data source Bertina's weather page uses).

```python
from bertina.weather import BertinaWeather

with BertinaWeather() as client:
    forecast = client.forecast("Tehran")
    print(forecast.current.temperature)   # 22.0
    print(forecast.current.condition)     # عمدتاً صاف
    print(forecast.current.humidity)      # 45
    print(forecast.current.wind_speed)    # 10.0
```

**Daily forecast:**
```python
with BertinaWeather() as client:
    forecast = client.forecast("اصفهان")
    for day in forecast.daily:
        print(day.date, day.temp_max, day.temp_min, day.condition)
```

**Hourly forecast:**
```python
with BertinaWeather() as client:
    forecast = client.forecast("Tehran")
    for hour in forecast.hourly[:6]:
        print(hour.time, hour.temperature, hour.condition)
```

**Async:**
```python
from bertina.weather import AsyncBertinaWeather

async with AsyncBertinaWeather() as client:
    forecast = await client.forecast("مشهد")
    print(forecast.location, forecast.latitude, forecast.longitude)
```

**`WeatherForecast`**
```
location    — resolved city name (in Persian if available)
latitude    — GPS latitude
longitude   — GPS longitude
current     — WeatherCurrent object
hourly      — list[WeatherHour] (168 hours / 7 days)
daily       — list[WeatherDay] (7 days)
```

**`WeatherCurrent`**
```
temperature    — current temperature (°C)
feels_like     — apparent temperature (°C)
humidity       — relative humidity (%)
wind_speed     — wind speed (km/h)
wind_direction — wind direction (degrees)
condition      — weather description in Persian (e.g. "عمدتاً صاف")
pressure       — surface pressure (hPa)
visibility     — visibility (metres)
uv_index       — UV index
precipitation  — current precipitation (mm)
```

**`WeatherDay`**
```
date                     — date string (e.g. "2024-01-01")
temp_max                 — max temperature (°C)
temp_min                 — min temperature (°C)
condition                — weather description in Persian
precipitation_probability — max precipitation probability (%)
sunrise                  — sunrise time string
sunset                   — sunset time string
```

**`WeatherHour`**
```
time                     — datetime string (e.g. "2024-01-01T14:00")
temperature              — temperature (°C)
condition                — weather description in Persian
precipitation_probability — precipitation probability (%)
```

---

## Client Options

All clients accept these parameters:

```python
BertinaSearch(
    timeout=15.0,        # request timeout in seconds
    headers={},          # override or extend default headers
    proxy="http://...",  # HTTP/SOCKS proxy URL
    debug=False,         # attach raw HTML to responses
    cache_ttl=300,       # cache lifetime in seconds
    max_retries=3,       # retry attempts on failure
)

AsyncBertinaSearch(
    # all of the above, plus:
    max_concurrent=5,    # max simultaneous async requests
)
```

**Debug mode:**
```python
with BertinaSearch(debug=True) as client:
    resp = client.search("python")
    print(resp._raw_html[:500])    # raw HTML from the server
```

**Custom cache TTL:**
```python
# Cache search results for 10 minutes
with BertinaSearch(cache_ttl=600) as client:
    resp = client.search("python")
```

---

## Bot Detection Avoidance

The library is designed to appear as a real Chrome browser to avoid bot detection:

- **TLS fingerprint** — uses [`curl_cffi`](https://github.com/yifeikong/curl-cffi) to impersonate Chrome 124 at the TLS/JA3 level, matching the exact handshake a real browser sends
- **Browser headers** — `sec-ch-ua`, `Sec-Fetch-*`, `Accept`, `Accept-Encoding` are set automatically and consistently by the impersonation profile
- **Correct `Accept-Language`** — `en,fa;q=0.9` (taken from real HAR captures of the site)
- **`Referer` header** — search, places, and radar clients send `https://search.bertina.ir/` as the referer, matching real browser navigation
- **Request pacing** — a random delay of 1.5–3.5 s is added before every real HTTP request (cache hits are instant); additionally a longer pause of 30–300 s is triggered after every 10–70 requests to mimic natural browsing sessions

No configuration is required — all of this is on by default.

---

## Error Handling

```python
from bertina import BertinaHTTPError, BertinaParseError, BertinaRateLimitError

try:
    with BertinaSearch() as client:
        resp = client.search("python")
except BertinaRateLimitError:
    print("Rate limited — wait and retry")
except BertinaHTTPError as e:
    print(f"HTTP error {e.status_code}")
except BertinaParseError as e:
    print(f"Failed to parse response: {e}")
```

---

## DNS

Bertina provides a free DNS service that unblocks international websites.
Set your DNS server to:

```
193.186.32.32
```

The IP is also available as a constant:
```python
from bertina import DNS_IP
print(DNS_IP)  # 193.186.32.32
```

---

## Roadmap

**Phase 1 (current)**
- [x] `bertina.search` — all 7 search types + website alive check
- [x] `bertina.radar` — news radar
- [x] `bertina.places` — business directory (32 provinces, 1,014 cities)
- [x] `bertina.translate` — translation (34 languages)
- [x] `bertina.weather` — weather forecasts (open-meteo.com)

**Phase 2 (planned)**
- [ ] `bertina.llm` — AI assistant (llm.bertina.ir)
- [ ] `bertina.mail` — email client (bertinamail.com)
- [ ] `bertina.ads` — advertising platform (ads.bertina.ir)

---

## Project Structure

```
src/bertina/
├── __init__.py        — top-level exports and version
├── _base.py           — shared HTTP client (curl_cffi, retry, cache, pacing)
├── _parsers.py        — shared HTML parsing helpers
├── constants.py       — service URLs, headers, DNS IP
├── exceptions.py      — BertinaError hierarchy
├── search/            — search module (7 types + alive check)
├── radar/             — news radar module
├── places/            — places directory module
├── translate/         — translation module (34 languages)
└── weather/           — weather module (open-meteo.com)

tests/
├── conftest.py        — shared fixture loader + no_sleep autouse fixture
├── search/            — parser + client tests, 7 HTML fixtures
├── radar/             — parser + client tests, 1 HTML fixture
├── places/            — parser + client tests, 4 HTML fixtures
├── translate/         — client tests (13 tests)
└── weather/           — client tests (10 tests)
```

---

## License

See [LICENSE](LICENSE).
