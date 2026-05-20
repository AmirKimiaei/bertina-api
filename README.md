# bertina-py

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

---

## Installation

```bash
# Clone the repo
git clone https://github.com/Amir_Kimiaei/bertina-py.git
cd bertina-py

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows

# Install
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

## Client Options

All clients accept these parameters:

```python
BertinaSearch(
    timeout=15.0,        # request timeout in seconds
    headers={},          # override default headers
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
- [ ] `bertina.places` — business directory
- [ ] `bertina.translate` — translation (34 languages)
- [ ] `bertina.weather` — weather forecasts

**Phase 2 (planned)**
- [ ] `bertina.llm` — AI assistant (llm.bertina.ir)
- [ ] `bertina.mail` — email client (bertinamail.com)
- [ ] `bertina.ads` — advertising platform (ads.bertina.ir)

---

## Project Structure

```
src/bertina/
├── __init__.py        — top-level exports and version
├── _base.py           — shared HTTP client (retry, cache, rate limiter)
├── _parsers.py        — shared HTML parsing helpers
├── constants.py       — service URLs, headers, DNS IP
├── exceptions.py      — BertinaError hierarchy
├── search/            — search module
├── radar/             — news radar module
├── places/            — places module (coming soon)
├── translate/         — translation module (coming soon)
└── weather/           — weather module (coming soon)
```

---

## License

See [LICENSE](LICENSE).
